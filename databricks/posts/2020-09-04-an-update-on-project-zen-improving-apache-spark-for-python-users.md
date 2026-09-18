# An Update on Project Zen: Improving Apache Spark for Python Users

- Source: https://www.databricks.com/blog/2020/09/04/an-update-on-project-zen-improving-apache-spark-for-python-users.html
- Published: 2020-09-04
- Authors: Hyukjin Kwon, Matei Zaharia
- Categories: solutions, engineering, open-source
- Images: 1 total, 1 extracted as architecture

Apache Spark™ has reached its 10th anniversary with [Apache Spark 3.0](https://www.databricks.com/blog/2020/06/18/introducing-apache-spark-3-0-now-available-in-databricks-runtime-7-0.html) which has many significant improvements and new features including but not limited to [type hint support in pandas UDF](https://www.databricks.com/blog/2020/05/20/new-pandas-udfs-and-python-type-hints-in-the-upcoming-release-of-apache-spark-3-0.html), better error handling in UDFs, and Spark SQL [adaptive query execution](https://www.databricks.com/blog/2020/05/29/adaptive-query-execution-speeding-up-spark-sql-at-runtime.html). It has grown to be one of the most successful open-source projects as the de facto unified engine for data science.  In fact, Apache Spark has now reached the plateau phase of the [Gartner Hype cycle](https://www.gartner.com/en/documents/3988118) in data science and machine learning pointing to its enduring strength.

As Apache Spark grows, the number of PySpark users has grown rapidly. [68% of notebook commands on Databricks are in Python](https://www.databricks.com/blog/2020/06/18/introducing-apache-spark-3-0-now-available-in-databricks-runtime-7-0.html). The number of PySpark users has almost [jumped up three times for the last year](https://pypistats.org/packages/pyspark). The Python programming language itself became one of the most commonly used languages in data science.

With this momentum, the Spark community started to focus more on Python and PySpark, and in an initiative [we named](https://www.databricks.com/session_na20/wednesday-morning-keynotes)[Project Zen](https://issues.apache.org/jira/browse/SPARK-32082), named after [The Zen of Python](https://www.python.org/dev/peps/pep-0020/) that defines the principles of Python itself.

This blog post introduces Project Zen and our future plans for PySpark development focusing on the following upcoming features:

- Redesigning PySpark documentation
- PySpark type hints
- Visualization
- Standardized warnings and exceptions
- JDK, Hive and Hadoop distribution option for PyPI users

## Redesigning PySpark documentation

The structure and layout of the PySpark documentation have not been updated for more than five years, since the days when RDD was the only user-facing API It had focused more on being a development reference rather than readability. For example, it listed all classes and methods in a single page. It does not have a user guide or quickstart, and it is difficult to navigate.

As part of Project Zen, redesigning PySpark documentation is now under heavy development to provide users not only structured API references as well as meaningful examples, scenarios, and quickstart guides - but also dedicated migration guides and advanced use cases.The demonstration of the new PySpark documentation was [introduced in the SAIS 2020 keynote](https://www.databricks.com/session_na20/wednesday-morning-keynotes).

 

   *Demonstration of new PySpark documentation*

 

 

In addition, the docstrings will follow [numpydoc](https://numpydoc.readthedocs.io/en/latest/) style (ref: [SPARK-32085](https://issues.apache.org/jira/browse/SPARK-32085)) as the current PySpark docstrings and the generated HTML pages are less readable.

Switching it to [numpydoc](https://numpydoc.readthedocs.io/en/latest/) enables us to have a better docstring; for example, this hint:

becomes a more readable docstring in the [numpydoc](https://numpydoc.readthedocs.io/en/latest/) style as below:

Moreover, it generates more readable and structured API references in HTML as noted in [this example](https://numpydoc.readthedocs.io/en/latest/example.html#module-example).

## PySpark type hints

An important roadmap item is [Python type hint support in PySpark APIs](https://issues.apache.org/jira/browse/SPARK-32681). Python type hints were officially introduced in [PEP 484](https://www.python.org/dev/peps/pep-0484/) with Python 3.5 to statically indicate the type of a value in Python, and leveraging it has multiple benefits such as auto-completion, IDE support, automated documentation, etc.

This type hint support in PySpark APIs was [implemented as a third party](https://github.com/zero323/pyspark-stubs), and we’re currently working to officially port it into PySpark to improve usability in PySpark. This is now in the roadmap for the upcoming Apache Spark 3.1.

With the type hint support users will be able to do static error detection and autocompletion as shown below:

 

   *Static error detection*

 

 

 

 

   *Improved autocompletion*

 

 

## Visualization

Visualizing data is a critical component of data science as it helps people understand trends at a glance and make informed decisions quickly. Currently, there is no native visualization support in PySpark, so developers generally just call `DataFrame.summary()` to get a table of numbers and downsampling a subset of their data to visualize it with libraries such as [matplotlib](https://matplotlib.org/3.3.1/contents.html) and [Koalas](https://koalas.readthedocs.io/en/latest/getting_started/10min.html#Plotting), or rely on other third-party business intelligence and big data analytics tools.

Visualization support is in the roadmap of Project Zen for PySpark to directly support APIs to plot users’ DataFrames. [Koalas already implements](https://koalas.readthedocs.io/en/latest/getting_started/10min.html#Plotting) plotting from a Spark DataFrame (see example below), and this can be easily leveraged to bring the visualization support into PySpark.

*Plotting Spark DataFrame by using Koalas*

**Summary:** A Koalas plot of four stepwise data series labeled A, B, C, and D.

**Components:**

- A: plotted data series
- B: plotted data series
- C: plotted data series
- D: plotted data series

**Flows:**

- none

**Numbers:** none

```mermaid
%% Shows four plotted data series labeled A, B, C, and D
flowchart LR
    A[A]
    B[B]
    C[C]
    D[D]

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class A client
    class B service
    class C store
    class D critical
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2020/09/blog-project-zen-1.png</sub>

   *Plotting Spark DataFrame by using Koalas*

 

 

## Standardized warnings and exceptions

PySpark error and warning types are obscure and vaguely classified. When users face an exception or a warning, often it is a plain Exception or UserWarning. For example,

This makes it difficult for users to programmatically take an action on the exception, for example by try-except syntax.

It is now in the roadmap to define the classification of exceptions and fined-grained warnings so that users can expect which exceptions and warnings are issued for which case, and take the corresponding action appropriately.

## JDK, Hive and Hadoop distribution option for PyPI users

`pip` is a very easy way to install PySpark with [more than 5 million downloads every month from PyPI](https://pypistats.org/packages/pyspark). Users just type `pip install pyspark`, and run PySpark shells or submit an application to the cluster. At the same time, Apache Spark introduced many profiles to consider when distributing, for example, JDK 11, Hadoop 3, and Hive 2.3 support.

Unfortunately, PySpark only supports one combination by default when it is downloaded from PyPI: JDK 8, Hive 1.2, and Hadoop 2.7 as of Apache Spark 3.0.

As part of Project Zen, the distribution option will be provided to users so users can select the profiles they want. Users will be able to simply install from PyPI and use any existing Spark cluster. This is being tracked at [SPARK-32017](https://issues.apache.org/jira/browse/SPARK-32017).

## What’s next?

Project Zen is in progress thanks to the tremendous efforts from the community. PySpark documentation, PySpark type hints, and optional profiles in the PyPI distribution are targeted to be introduced for the upcoming Apache Spark 3.1. Other items that are under heavy development will be introduced in a later Spark release.

Apache Spark places more importance on PySpark and Python than ever and will keep improving its usability as well as its performance to help Python developers and data scientists become even more successful when working with Spark.
