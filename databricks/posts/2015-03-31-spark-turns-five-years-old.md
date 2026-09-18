# Apache Spark Turns Five Years Old!

- Source: https://www.databricks.com/blog/2015/03/31/spark-turns-five-years-old.html
- Published: 2015-03-31
- Authors: Matei Zaharia
- Categories: engineering, open-source
- Images: 1 total, 1 extracted as architecture

Today, we’re celebrating an important milestone for the Apache Spark project -- it’s now been five years since Spark was [first open sourced](https://github.com/apache/spark/commit/df29d0ea4c8b7137fdd1844219c7d489e3b0d9c9). When we first decided to release our research code at UC Berkeley, none of us knew how far Spark would make it, but we believed we had built some really neat technology that we wanted to share with the world. In the five years since, we’ve been simply awed by the numerous contributors and users that have made Spark the leading-edge computing framework it is today. Indeed, to our knowledge, Spark has now become the most active open source project in big data (looking at either contributors per month or commits per month). In addition to contributors, it has built up an array of [hundreds of production use cases](https://www.databricks.com/blog/2015/01/27/big-data-projects-are-hungry-for-simpler-and-more-powerful-tools-survey-validates-apache-spark-is-gaining-developer-traction.html) from batch analytics to stream processing.

**Summary:** The chart shows monthly growth in Apache Spark contributors from 2010 through 2014.

**Components:**

- Chart title: Growth of Spark contributors in the past 5 years
- Y-axis: Contributors per month
- X-axis: Years 2010 through 2014
- Blue vertical bars: Monthly contributor counts

**Flows:**

- none

**Numbers:** 5 years; 0, 20, 40, 60, 80, 100, 120, 140 contributors per month; 2010, 2011, 2012, 2013, 2014

```text
%% mermaid failed to render; kept as text
%% Shows monthly Apache Spark contributor growth from 2010 through 2014
flowchart LR
    T[Growth of Spark contributors in the past 5 years]
    Y[Contributors per month]
    B[Blue monthly contributor bars]
    X[Years]
    YR[2010 2011 2012 2013 2014]

    T --> B: chart title
    Y --> B: vertical scale
    B --> X: monthly values
    X --> YR: time axis

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class T client
    class Y service
    class B store
    class X cache
    class YR external
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2015/03/Screen-Shot-2015-03-31-at-7.51.18-AM.png</sub>

To celebrate Spark’s fifth birthday, one thing I wanted to do was to highlight some of the key ideas behind how we built out the project that still apply today. To do this, I took another look at the [first public version of Spark](https://github.com/apache/spark/tree/df29d0ea4c8b7137fdd1844219c7d489e3b0d9c9).

The first thing to notice is that this version was quite small: it weighed in at 3900 lines of code, of which 1300 were the Scala interpreter, 600 were examples and 300 were tests. Since March 2010, I’m happy to say that our test coverage has gone up substantially. However, the observation about size does reflect something important: since the beginning, we’ve sought to keep the Spark engine small and compact, making it easier for many developers to understand and for us to change and improve. Even today, the core Spark engine is only about 50,000 lines of code. The main additions since that first version have been support for “shuffle” operations, which required new networking code and a DAG scheduler, as well as support for multiple backend schedulers, such as YARN. Nonetheless, even today we can regularly make large changes to the core engine that improve the performance or stability of all Spark applications. For example, during our work last year on [large-scale sorting](https://www.databricks.com/blog/2014/10/10/spark-petabyte-sort.html), multiple developers at Databricks ended up rewriting almost all of Spark’s networking layer.

The second thing to notice about Spark from 2010 is what it can do: even this ~2000 line engine could handle two of the most important workloads for Spark today, iterative algorithms and interactive queries. Back in 2010, we were the only cluster computing engine to support interactive use, by modifying the Scala interpreter to submit code to a Spark cluster. We’ve constantly sought to improve this experience and enable truly interactive data science through features like Spark’s [Python API](https://spark.apache.org/examples.html) and [DataFrames](https://www.databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html). In addition, even the 2010 version of Spark was able to run iterative algorithms like [logistic regression](https://github.com/apache/spark/blob/df29d0ea4c8b7137fdd1844219c7d489e3b0d9c9/src/examples/SparkHdfsLR.scala) 20-30x faster than MapReduce (subsequent improvements brought this up to 100x).

A final important element in how we think about the project is our focus on simple, stable APIs. The code examples that ship with Spark from 2010, like [logistic regression](https://github.com/apache/spark/blob/df29d0ea4c8b7137fdd1844219c7d489e3b0d9c9/src/examples/SparkHdfsLR.scala) and [computing pi](https://github.com/apache/spark/blob/df29d0ea4c8b7137fdd1844219c7d489e3b0d9c9/src/examples/SparkPi.scala), are nearly identical to Spark code from today (see [logistic regression](https://github.com/apache/spark/blob/master/examples/src/main/scala/org/apache/spark/examples/SparkHdfsLR.scala), [pi](https://github.com/apache/spark/blob/master/examples/src/main/scala/org/apache/spark/examples/SparkPi.scala)). We work very hard to define stable APIs that developers can build on years into the future, minimizing the work they must do to keep up with improvements in Spark. Starting in Apache Spark 1.0, these compatibility guarantees are now [formalized](https://cwiki.apache.org/confluence/display/SPARK/Spark+Versioning+Policy) for all major Spark components.

That’s enough about Spark in 2010. How has the project grown since then? While there has been tremendous activity in all areas of Spark, including support for more programming languages (Java, Python and soon R), data sources, and optimizations, the single biggest addition to Spark has been its standard libraries. Over the years, Spark has acquired four high-level libraries -- [Spark Streaming](https://spark.apache.org/streaming/), [MLlib](https://spark.apache.org/mllib/), [GraphX](https://spark.apache.org/graphx/) and [Spark SQL](https://spark.apache.org/sql/) -- that all run on top of the core engine, and interoperate easily and efficiently with each other. Today these libraries are the bulk of the code in Spark -- about 200,000 lines compared to 50,000 in the core engine. They also represent the single largest standard library available for big data, making it easy to write applications that span all stages of the data lifecycle. Nevertheless, these libraries are still quite new, the majority of them having been added in the last two years. In future years I expect these libraries to grow significantly, with the aim to build as rich a toolset for big data as the libraries available for small data. You can find some of the areas where Databricks is working on these libraries in my [slides from Spark Summit 2015](https://www.databricks.com/dataaisummit).

Finally, like any five-year-old, Spark is still sometimes able to get into trouble without supervision and sometimes hard to understand. At Databricks, we’re working hard to make Spark easier to use and run than ever, through our efforts on both the Spark codebase and support materials around it. All of our work on Spark is open source and goes directly to Apache. In addition, we have put up a large array of free online training materials, as well as [training courses](https://academy.databricks.com/) and [books](https://www.oreilly.com/library/view/~/9781449359034/). Finally, we have built a service to make it very easy to run Spark in a few clicks, [Databricks Cloud](https://www.databricks.com/product/data-lakehouse). We hope that you enjoy using Spark, no matter which environment you run it in, as much as we enjoy building it.
