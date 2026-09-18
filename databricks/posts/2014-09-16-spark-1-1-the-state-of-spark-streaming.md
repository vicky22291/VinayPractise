# Apache Spark 1.1: The State of Spark Streaming

- Source: https://www.databricks.com/blog/2014/09/16/spark-1-1-the-state-of-spark-streaming.html
- Published: 2014-09-16
- Authors: Tathagata Das, Patrick Wendell
- Categories: engineering, data-engineering, open-source
- Images: 0 total, 0 extracted as architecture

With Apache Spark 1.1 recently released, we’d like to take this occasion to feature one of the most popular Spark components - Spark Streaming - and highlight who is using Spark Streaming and why.

Apache Spark 1.1. adds several new features to Spark Streaming.  In particular, Spark Streaming extends its library of ingestion sources to include Amazon Kinesis, a hosted stream processing engine, as well as to provide high availability for Apache Flume sources.  Moreover, Apache Spark 1.1 adds the first of a set of online machine learning algorithms with the introduction of a streaming linear regression.

Many organizations have evolved from exploratory, discovery use cases of big data to use cases that require reasoning on data as it arrives in order to make decisions in real time.  Spark Streaming enables this category of high-value use cases, providing a system for processing fast and large streams of data in real time.

**What is it?**

Spark Streaming is an extension of the core Spark API that enables high-throughput, reliable processing of live data streams. Spark Streaming ingests data from any source including Amazon Kinesis, Kafka, Flume, Twitter and file systems such as S3 and [HDFS](https://www.databricks.com/glossary/hadoop-distributed-file-system-hdfs).  Users can express sophisticated algorithms easily using high-level functions to process the data streams.  The core innovation behind Spark Streaming is to treat streaming computations as a series of deterministic micro-batch computations on small time intervals, executed using Spark's distributed data processing framework.  Micro-batching unifies the programming model of streaming with that of batch use cases and enables strong fault recovery guarantees while retaining high performance.  The processed data can then be stored in any file system (including HDFS), database (including Hbase), or live dashboards.

**Where is it being used?**

Spark Streaming has seen a significant uptake in adoption in the past year as enterprises increasingly use it as part of Spark deployments.  The Databricks team is aware of more than 40 organizations that have deployed Spark Streaming in production.

Just as impressive is the breadth of industries across which Spark Streaming is being used.  For instance:

- A leading software vendor leverages Spark Streaming to power its **real-time supply chain analytics platform**, which provides more than 1,000 supplier performance metrics to users via dashboards and detailed operational reports.
- A large **hardware vendor** is using Spark Streaming for security intelligence operations, notably a first check of known threats.
- A leading **advertising** technology firm is processing click stream data for its real-time ad auction platform, leading to more accurate targeting of display advertising, better consumer engagement and higher conversion.
- A global **telecommunications** provider is collecting metrics from millions of mobile phones and analyzing them to determine where to place new cell phone towers and upgrade aging infrastructure, resulting in improved service quality.
- A pre-eminent video analytics provider is using Spark Streaming to help **broadcasters and media companies** monetize video with personalized, interactive experiences for every screen.

We’ve seen Spark Streaming benefit many parts of an organization, as the following examples illustrate:

- **Marketing & Sales**:  Analysis of customer engagement and conversion, powering real-time recommendations while customers are still on the site or in the store.
- **Customer Service & Billing**:  Analysis of contact center interactions, enabling accurate remote troubleshooting before expensive field technicians are dispatched.
- **Manufacturing**: Real-time, adaptive analysis of machine data (e.g., sensors, control parameters, alarms, notifications, maintenance logs, and imaging results) from industrial systems (e.g., equipment, plant, fleet) for visibility into asset health, proactive maintenance planning, and optimized operations.
- **Information Technology**:  Log processing to detect unusual events occurring in streams of data, empowering IT to take remedial action before service quality degrades.
- **Risk Management**:  Anomaly detection and root cause forensics, which sometimes makes it possible to stop fraud while it happens.

**Why is it being used?**

The reasons enterprises give for adopting (and in many cases transitioning to) Spark Streaming often start with the advantages that Spark itself brings.  All the strengths of Spark’s unified programming model apply to Spark Streaming, which is particularly relevant for real-time analytics that combine historical data with fresh data:

- **Making data science accessible to non-scientists**:  Spark’s declarative APIs enable users who have domain expertise but lack data science expertise to express a business problem and its associated processing algorithm and data pipeline using simple high-level operators.
- **Higher productivity for data workers**:  Spark’s write-once-run-anywhere approach unifies batch and stream processing.  In fact, Spark ties together the different parts of an analytics pipeline in the same tool, such as discovery, ETL, data engineering, machine learning model training and execution, across all types of structured and unstructured data.
- **Exactly-once semantics: ** Many business critical use cases have a need for exactly-once stateful processing, not at-most-once (which includes zero) or at-least-once (which includes duplicates).  Exactly-once provides users with certainty on questions such as the exact number of frauds, emergencies or outages occurring today.
- **No compromises on scalability and throughput**.  Spark Streaming is designed for hyper-scale environments and combines statefulness and persistence with high throughput.
- **Ease of operations**:  Spark provides a unified run time across different processing engines.  One physical cluster and one set of operational processes covers the full spectrum of use cases.

We have also learned from the community that the high throughput that Spark Streaming provides is just as important as latency.  In fact, latency of a few hundred milliseconds is sufficient for the vast majority of streaming use cases.  Rare exceptions include algorithmic trading.

One capability that allows Spark Streaming to be deployed in such a wide variety of situations is that users have a choice of three resource managers:  Full integration with YARN and Mesos as well as the ability to rely on Spark’s easy-to-use stand-alone resource manager.  Moreover, Spark and Spark Streaming are supported already by leading vendors such as Cloudera, MapR and Datastax.  We expect other vendors will include and support Spark in their Hadoop distributions in the near future.

Please stay tuned for future posts on Spark Streaming technical design patterns and practical use cases.
