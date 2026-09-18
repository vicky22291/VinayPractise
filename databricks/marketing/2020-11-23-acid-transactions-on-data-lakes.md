# ACID Transactions on Data Lakes Tech Talks: Getting Started with Delta Lake

- Source: https://www.databricks.com/blog/2020/11/23/acid-transactions-on-data-lakes.html
- Published: 2020-11-23
- Authors: Ryan Boyd
- Categories: platform, solutions, engineering
- Images: 2 total, 0 extracted as architecture

Get an [early preview of O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=acidtransactionsdatalakes-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

---

As part of our Data + AI Online Meetup, we’ve explored topics ranging from genomics (with guests from Regeneron) to machine learning pipelines and GPU-accelerated ML to Tableau performance optimization. One key topic area has been an exploration of the Lakehouse.

The rise of the Lakehouse architectural pattern is built upon tech innovations enabling the data lake to support ACID transactions and other features of traditional data warehouse workloads.

The [Getting Started with Delta Lake](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks) tech talk series takes you through the technology foundation of Delta Lake (Apache Spark™), building highly scalable data pipelines, tackling merged streaming + batch workloads, powering data science with Delta Lake and MLflow, and even goes behind the scenes with Delta Lake engineers to understand the origins.

### [Making Apache Spark Better with Delta Lake](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks/making-apache-spark-better-with-delta-lake)

Apache Spark is the dominant processing framework for big data. Delta Lake adds reliability to Spark so your analytics and machine learning initiatives have ready access to quality, reliable data stored in low-cost cloud object stores such as AWS S3, Azure Storage, and Google Cloud Storage. In this session, you’ll learn about using Delta Lake to enhance data reliability for your data lakes.

### [Simplify and Scale Data Engineering Pipelines](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks/simplify-scale-data-engineering-pipelines)

A common data engineering pipeline architecture uses tables that correspond to different quality levels, progressively adding structure to the data: data ingestion (“Bronze” tables), transformation/feature engineering (“Silver” tables), and aggregate tables/machine learning training or prediction (“Gold” tables). Combined, we refer to these tables as a “multi-hop” architecture. It allows data engineers to build a pipeline that begins with raw data as a “single source of truth” from which everything flows. In this session, you’ll learn about the data engineering pipeline architecture, data engineering pipeline scenarios and best practices, how Delta Lake enhances data engineering pipelines, and how easy adopting Delta Lake is for building your data engineering pipelines.

### [Beyond Lambda: Introducing Delta Architecture](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks/beyond-lambda-introducing-delta-architecture)

Lambda architecture is a popular technique where records are processed by a batch system and streaming system in parallel. The results are then combined during query time to provide a complete answer. With the advent of Delta Lake, we are seeing a lot of our customers adopting a simple continuous data flow model to process data as it arrives. We call this architecture the “Delta Architecture.” In this session, we cover the major bottlenecks for adopting a continuous data flow model and how the Delta Architecture solves those problems.

### [Getting Data Ready for Data Science with Delta Lake and MLflow](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks/getting-data-ready-data-science-delta-lake-mlflow)

When it comes to planning for data science initiatives, one must take a holistic view of the entire data analytics realm. Data engineering is a key enabler of data science that helps furnish reliable, quality data in a timely fashion.  In this session, you will learn about the data science lifecycle, key tenets of modern data engineering, how Delta Lake can help make reliable data ready for analytics, how easy it is to adopt Delta Lake to power your data lake, and how to incorporate Delta Lake within your data infrastructure to enable Data Science.

### [Behind the Scenes: Genesis of Delta Lake](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks/behind-the-scenes-genesis-of-delta-lake)

Developer Advocate Denny Lee interviews Burak Yavuz, Software Engineer at Databricks, to learn about the Delta Lake team’s decision making process and why they designed, architected, and implemented the architecture that it is today. In this session, you’ll learn about technical challenges that the team faced, how those challenges were solved, and what their plans are for the future.

### Get Started

Get Started filling your Delta Lake today by watching this [complete series](https://www.databricks.com/discover/getting-started-with-delta-lake-tech-talks).

### What’s Next?

If you want to expand your knowledge on Delta Lake, watch our [Diving into Delta Lake](https://www.databricks.com/discover/diving-into-delta-lake-talks) tech talk series. Guided by the Delta Lake engineering team, including Burak Yavuz, Andrea Neumann, Tathagata “TD” Das, and Developer Advocate, Denny Lee,  you will learn about the internal implementation of Delta Lake.

If you want to hear about future online meetups, join our [Data + AI Online Meetup](https://www.meetup.com/data-ai-online/?_cookie-check=jg5JIxoASzYoE36c) on meetup.com

**Diving into Delta Lake**
 Immerse yourself in the internals of Delta Lake, a popular open source technology for more reliable data lakes.

[Watch Now](https://www.databricks.com/discover/diving-into-delta-lake-talks)
