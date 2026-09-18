# On-Demand Webinar: Geospatial Analytics and AI in the Public Sector

- Source: https://www.databricks.com/blog/2020/01/28/geospatial-analytics-public-sector-webcast.html
- Published: 2020-01-28
- Authors: Michael Johns, Derek Yeager
- Categories: solutions, engineering, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

We recently hosted a live webinar — [Geospatial Analytics and AI in Public Sector](https://pages.databricks.com/201912-WB-PubSec-Geospatial-Analytics_01.On-demandpage.html)— during which we covered top geospatial analysis use cases in the Public Sector along with live demos showcasing how to build scalable analytics and machine learning pipelines on geospatial data at sale.

## Geospatial Analytics Webinar Overview

Today, government agencies have access to massive volumes of geospatial information that can be analyzed to deliver on a broad range of decision-making and [predictive analytics](https://www.databricks.com/glossary/predictive-analytics) use cases from transportation planning to disaster recovery and population health management.

While many agencies have invested in geographic information systems that produce volumes of geospatial data, few have the proper technology and technical expertise to prepare these large, complex datasets for analytics — inhibiting their ability to build AI applications.

**In this webinar, we reviewed:**

- Top geospatial big data use cases in Public Sector spanning public safety, defense, infrastructure management, health services, fraud prevention and more
- Challenges analyzing large volumes of geospatial data with legacy architectures
- How Databricks and open-source tools can be used to overcome these challenges in the cloud
- Technical demos and notebooks shared on the webinar:
  - Object Detection in xView Imagery: Bridges complex object detection using Deep Learning with accessible SQL-based analytics for non-data scientist personas. Download related notebooks: [data engineering](https://www.databricks.com/notebooks/1_data_eng_xview_object_detection.html) and [analysis](https://www.databricks.com/notebooks/2_analysis_xview_object_detection.html).
  - Processing Large-Scale NYC Taxi Pickup / Dropoff Vectors: Optimizes geospatial predicate operations and joins to associate raw pick-up/drop-off coordinates with their corresponding NYC neighborhood boundaries to facilitate spatial analysis. [Download related notebook](https://www.databricks.com/notebooks/GeoMesa-NYC-Taxis.html).

If you’d like free access to the [Unified Data Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free Databricks trial here](https://www.databricks.com/try-databricks).

 

**At the end of the webinar we held a Q&A. Below are the questions and answers: **

 

**Q: We deal with large volumes of streaming geospatial data. How would you recommend handling these real-time data streams for downstream analytics?**

**A:** This can be broken down to (1) handling large volumes of streaming data and (2) performing downstream geospatial analytics. Databricks makes processing and storing large volumes of streaming data simple, reliable, and performant. Please reference [Delta Lake on Databricks](https://www.databricks.com/product/delta-lake-on-databricks) and [Introduction to Delta Lake](https://docs.databricks.com/delta/delta-streaming.html#table-streaming-reads-and-writes) for some additional material. The second part builds on storage and schema decisions made during the processing phase. Spatial analysis is fundamentally addressed through the use of[Spark SQL, DataFrames, and Dataset](https://spark.apache.org/docs/latest/sql-programming-guide.html)s to power transformations and actions over data originating from various formats and schemas. Databricks offers various runtimes such as [Machine Learning Runtime](https://www.databricks.com/product/machine-learning-runtime) and [Databricks Runtime with Conda](https://docs.databricks.com/runtime/conda.html) which pre-bundle popular libraries including Tensorflow, Horovod, PyTorch, Scikit-Learn, and Anaconda for both CPU and GPU clusters to facilitate common Data Engineering and Data Science needs. Customers can also manage their own [Libraries](https://docs.databricks.com/libraries/index.html#libraries) or [Containers](https://docs.databricks.com/clusters/custom-containers.html#customize-containers-with-databricks-container-services) to customize the environment for any analytic, to include spatial specific needs. Please reference popular spatial frameworks listed in the following question as well as the FINRA Customer Case Study

**Q: What are some of the more popular spatial frameworks being used in the public sector?**

**A:** Popular frameworks which extend Apache Spark for geospatial analytics include [GeoMesa](https://github.com/locationtech/geomesa), [GeoTrellis](https://geotrellis.io/), [Rasterframes](https://rasterframes.io/), and [GeoSpark](https://sedona.apache.org/). In addition, Databricks makes it easy to use single-node libraries such as [GeoPandas](https://geopandas.org/en/stable/), [Shapely](https://github.com/shapely/shapely), [Geospatial Data Abstraction Library (GDAL)](https://gdal.org/), and [Java Topology Service (JTS)](https://github.com/locationtech/jts). By wrapping function calls in [user-defined functions (UDFs)](https://docs.databricks.com/spark/latest/spark-sql/udf-scala.html) these libraries can further be leveraged in a distributed context as well. UDFs offer a simple approach for scaling existing workloads with minimal code changes.

**Q: Where is my data stored and how does Databricks help ensure data security?**

**A:** Your data is stored in your own cloud data lake, such as in [AWS S3](https://docs.databricks.com/data/data-sources/aws/amazon-s3.html) or [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/databricks/data/data-sources/azure/azure-storage). However, data lakes often have data quality issues, due to a lack of control over ingested data. Delta Lake adds a storage layer to data lakes to manage data quality, ensuring data lakes contain only high-quality data for consumers. Delta Lake also offers capabilities like ACID transactions to ensure data integrity with serializability as well as audit history, allowing you to maintain log records details about every change made to data, providing a full history of changes, for compliance, audit, and reproduction. Additionally, Delta Lake has been designed to address various right-to-erasure initiatives such as the General Data Protection Regulation (GDPR) and recently the California Consumer Privacy Act (CCPA), reference [Make Your Data Lake CCPA Compliant with a Unified Approach to Data and Analytics](https://www.databricks.com/blog/2019/12/18/make-your-data-lake-ccpa-compliant.html). As part of our [Enterprise Cloud Service](https://www.databricks.com/product/enterprise-cloud-service), Delta Lake is tightly integrated with other Databricks Enterprise Security features.

## Additional Geospatial Analytics Resources

- Sign-up for a [free trial](https://www.databricks.com/try-databricks) and download these notebooks to start experimenting:
  - [Data Engineering: Object Detection with xView](https://www.databricks.com/notebooks/1_data_eng_xview_object_detection.html)
  - [Analysis: Object Detection with xView](https://www.databricks.com/notebooks/2_analysis_xview_object_detection.html)
  - [Analyzing NYC Taxis with GeoMesa](https://www.databricks.com/notebooks/GeoMesa-NYC-Taxis.html)
- Read our recent blog [Processing Geospatial Data at Scale With Databricks](https://www.databricks.com/blog/2019/12/05/processing-geospatial-data-at-scale-with-databricks.html) to learn how [Databricks Unified Data Analytics Platform](https://www.databricks.com/product/data-lakehouse) addresses challenges around ingesting, storing, and analyzing spatial data of massive size
- Download our [Guide to Data Analytics and AI at Scale for the Public Sector](https://www.databricks.com/p/ebook/a-guide-to-data-analytics-and-ai-at-scale)
- Visit our [Public Sector page](https://www.databricks.com/solutions/industries/federal-government) to learn how the Center for Medicare & Medicaid Services, DHS and other agencies are innovating with Databricks
