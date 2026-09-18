# A Guide to Developer, Deep Dive, and Continuous Streaming Applications Talks at Spark + AI Summit

- Source: https://www.databricks.com/blog/2019/02/19/a-guide-to-developer-deep-dive-and-continuous-streaming-applications-talks-at-spark-ai-summit.html
- Published: 2019-02-19
- Authors: Jules Damji
- Categories: data-streaming, company, news, events
- Images: 2 total, 0 extracted as architecture

In January 2013 when Stephen O’Grady, an analyst at [RedMonk](https://redmonk.com/), published [“The New Kingmakers: How Developers Conquered the World](https://thenewkingmakers.com/),” the book’s central argument (then and still now) universally resonated with an emerging open-source community. He convincingly charts developers’ movement “out of the shadows and into the light as new influencers on society’s [technical landscape].”

Using their choice of the open-source software and at-the-ready at studying or contributing source code on GitHub, developers have built data products using open-source technologies that have shaped the industry today. O’Grady cites notable open-source examples that engendered successful software companies as well as companies that employ open-source to build their infrastructure stacks.

He asserts that developers make a difference; they chart the course, like the Kingmakers.

And this April, you can join many of these kingmakers at [Spark + AI Summit 2019](https://www.databricks.com/sparkaisummit/north-america). Hear and learn from them as they offer their insight into use cases in how they combine data and AI, to build data pipelines as well as use and extend Apache Spark ™ to solve tough data problems.

In this blog, we highlight selected sessions that speak to developers’ endeavors in combining the immense value of data and AI across three tracks: Developer, Deep Dives, and Continuous Streaming Applications.

## Developer

Naturally, let’s start with the Developer track. Ryan Blue of Netflix in his talk, [*Improving Apache Spark's Reliability with DataSourceV2*](https://www.databricks.com/session/improving-apache-sparks-reliability-with-datasourcev2), will share Spark’s new DataSource V2 API, which allows working with data from tables and streams. With relevant changes to Spark SQL internals, the V2 allows developers to build reliable data pipelines from relevant data sources. For Spark developers writing data source connectors, this is a must talk to attend.

Enhanced in Spark 2.3, columnar storage is an efficient way to store DataFrames. In his talk, [*In-Memory Storage Evolution in Apache Spark*](https://www.databricks.com/session/in-memory-storage-evolution-in-apache-spark), Dr. Kazuaki Ishizaki, PMC member and an ACM award winner, will discuss the evolution of in-memory storage: How Apache Arrow exchange format and Spark’s ColumnVector for storage enhance Spark SQL access and query performance on DataFrames.

Related to DataFrames and Spark SQL, Messrs DB Tsai and Cesar Delgado of Apple Inc will address how they handle deeply nested structures by making them first-class citizens in Spark SQL, giving them immense speed up in querying and processing humongous data for Apple Siri, a virtual assistant. Their talk, [*Making Nested Columns as First Citizen in Apache Spark SQL*](https://www.databricks.com/session/making-nested-columns-as-first-citizen-in-apache-spark-sql), is a good example to show developers how to extend Spark SQL.

Which brings us Spark’s extensibility. Among many features that attract developers to Spark, one is its extensibility with new language bindings or libraries. Messrs Tyson Condie and Rahul Potharaju of Microsoft will explain how they extended Spark to include a new .NET bindings in their talk: [*Introducing .NET bindings for Apache Spark*](https://www.databricks.com/session/introducing-net-bindings-for-apache-spark).

Yet for all Spark’s many merits, fast-paced adoption and innovation from the wider community, developers face some challenges: how do you automate testing, assess the quality and performance of new developments? To that end Messers, Bogdan Ghit and Nicolas Poggi of Databricks will share their work in building a new testing and validating framework for Spark SQL in their talk: [*Fast and Reliable Apache Spark SQL Engine*](https://www.databricks.com/session/fast-and-reliable-apache-spark-sql-engine).

## Technical Deep Dives

Since its introduction in 2016 as a track with developer focused sessions, technical deep dives track has gained popularity in attendance. It attracts both data engineers and data scientists to get deeper experience on the subject. For example, this year three sessions stand out.

First, data privacy and protection have become imperative today, in light of [GDPR](https://eugdpr.org/), especially in Europe. [*Great Models with Great Privacy: Optimizing ML and AI Over Sensitive Data*](https://www.databricks.com/session/great-models-with-great-privacy-optimizing-ml-and-ai-over-sensitive-data-continues) talk from CTO Sim Simeonov of Swoop will challenge some technical assumptions that privacy asserts worse predictions in the ML models by examining some production environments techniques to mitigate this notion.

Second, Spark SQL is at the core of Spark’s structured APIs, including Structured Streaming, and its efficient query processing engine. But what enables it? What’s under the hood that’s performant and why? Messrs Maryann Xue and Takuya Ueshin of Databricks’ Apache Spark core team will dive into pipeline execution, whole-stage code generation, memory management, and internals that make this engine fault-tolerant and performant. A valuable lesson into the Spark core internals is their talk: [*A Deep Dive into Query Execution Engine of Spark SQL*](https://www.databricks.com/session/a-deep-dive-into-query-execution-engine-of-spark-sql).

And third, closely related to Spark SQL, is an effort to extend Spark to support Graph data in processing Spark SQL queries to enable data scientists and engineers to inspect and update graph databases. A proposed effort underway to integrate into Spark’s upcoming release, developers Alastair Green and Martin Junghanns from Neo4j will make the case for Cyhper, a graph querying language for Apache Spark in their talk: [*Neo4j Morpheus: Interweaving Table and Graph Data with SQL and Cypher in Apache Spark*](https://www.databricks.com/session/neo4j-morpheus-interweaving-table-and-graph-data-with-sql-and-cypher-in-apache-spark).

## Continuous Applications and Structured Streaming

Structured Streaming has garnered a lot of interest in building end-to-end data pipelines or writing continuous applications that interact in real-time with data and other applications. Three deep-dive talks will give you insight into how.

First is from Tathagata Das of Databricks: [*Designing Structured Streaming Pipelines—How to Architect Things Right*](https://www.databricks.com/session/designing-structured-streaming-pipelines-how-to-architect-things-right). Second is from Scott Klein of Microsoft: [*Using Azure Databricks, Structured Streaming & Deep Learning Pipelines, to Monitor 1,000+ Solar Farms in Real-Time*](https://www.databricks.com/session/headaches-and-breakthroughs-in-building-continuous-applications). And third is from Brandon Hamric of Eventbrite: [*Near real-time analytics with Apache Spark: Ingestion, ETL, and Interactive Queries*](https://www.databricks.com/session/near-real-time-analytics-with-apache-spark-ingestion-etl-and-interactive-queries).

## Apache Spark Training Sessions

And finally, check out two training courses for big data developers to extend your knowledge of Apache Spark programming, how to build scalable data pipelines with Delta, and performance and tunning respectively: [*APACHE SPARK™ PROGRAMMING AND DELTA*](https://www.databricks.com/sparkaisummit/north-america-2020/apache-spark-training) and [*APACHE SPARK™ TUNING AND BEST PRACTICES*](https://www.databricks.com/sparkaisummit/north-america-2020/apache-spark-training).

## What’s Next

You can also peruse and pick sessions from the [schedule](https://www.databricks.com/sparkaisummit/north-america-2020/agenda). In the next blog, we will share our picks from sessions related to Data Science and Data Engineering tracks.

If you have not registered yet, use this code **JulesPicks** and get 15% discount.

## Read More

- Read: [A Guide to AI, Machine Learning, and Deep Learning Talks at Spark + AI Summit](https://www.databricks.com/blog/2018/12/18/a-guide-to-ai-machine-learning-and-deep-learning-talks-at-spark-ai-2019.html)

__
