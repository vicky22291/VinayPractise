# How Collective Health uses Delta Live Tables and Structured Streaming for Data Integration

- Source: https://www.databricks.com/blog/2023/04/13/how-collective-health-uses-delta-live-tables-and-structured-streaming.html
- Published: 2023-04-13
- Authors: Mragesh Khandelwal, Mahmoud Saleh
- Categories: data-streaming, customers
- Images: 1 total, 0 extracted as architecture

[Collective Health](https://collectivehealth.com/) is not an insurance company. We're a technology company that's fundamentally making health insurance work better for everyone— starting with the 155M+ Americans covered by their employer.

We've created a powerful, flexible infrastructure to simplify employer-led healthcare, and started a movement that prioritizes the human experience within health benefits. We've built smarter technology that's easy to use, gives people an advocate in their health journey, and helps employers manage costs. It's a platform that's data-powered and human-empowered.

Our mission is to change the way people experience health benefits by making it effortless to understand, navigate, and pay for healthcare. By reducing the administrative lift of delivering health benefits, providing an intuitive member experience, and improving health outcomes, Collective Health guides employees toward healthier lives and companies toward healthier bottom lines.

One of the numerous offerings on our platform is [Premier Partner Program™](https://collectivehealth.com/solution/partner-ecosystem/premier-partner-program/), built on the Databricks Data + AI Platform. In this blog, we'll cover how we're making it easier to share data at scale with our partners.

## Pipeline Overview

Here is our integration architecture at a high level, in this post we will focus on the Delta Live Tables portion.

## Schema Definition

Before we begin with the ingest process we need to be explicit with our expectations from our partners. Since each partner might not have the capability of conforming to our internal schema we create a schema.

## Ingest Files

One of the benefits of working with [Apache Spark on Databricks](https://docs.databricks.com/spark/index.html) is the ability to read multiple files from a cloud storage provider.

We can read files into a PySpark DataFrame and save it into a delta table. We also included the ingest date and file name when ingesting the files that way we can revisit records should issues arise in the future.

This process worked well, but as business requirements changed so did the schema, new requirements arose, and columns that previously contained data now contained null values. We explored several solutions including implementing custom logic to handle invalid records. Out of the box Delta Live Tables provides us with validation tools, pipeline visualization, and a simple programmatic interface to do this. We also want to ingest files incrementally without having to go through each file we had previously ingested.

## Structured Streaming

We don't want to constantly listen for new files since we are expecting new data at a given schedule so our pipeline only needs to run at particular times. We can ingest new incoming files as they come in a similar fashion to an event driven model without having to keep our compute resources running all the time, instead we use the [Structured Streaming approach](https://www.databricks.com/product/data-streaming), for this we will use [Databricks' Auto Loader](https://docs.databricks.com/ingestion/auto-loader/index.html). Auto Loader creates a checkpoint file that keeps track of previously ingested files and records so we don't have to. We will also be exposing the _rescued_data column to capture records that did not get parsed based on the specified schema.

## Delta Live Tables

Setting up a [Delta Live Table (DLT)](https://www.databricks.com/product/delta-live-tables) pipeline is pretty straight forward. You would go ahead and setup your existing dataframe as a table

But before we go ahead and create the table we can validate that our records do not contain null values, for this we will refer back to the schema and identify required columns. We will use the [@dlt.expect_all](https://docs.databricks.com/workflows/delta-live-tables/delta-live-tables-expectations.html#multiple-expectations) decorator to keep track of records that fail this validation, this will not drop the records or fail the pipeline but we can use this to keep track of occurrences of null value in the non-nullable columns.

We do however want to drop records that have insufficient data or we are unable to validate. We will do this using the [@dlt.expect_or_drop](https://docs.databricks.com/workflows/delta-live-tables/delta-live-tables-expectations.html#multiple-expectations) decorator on a view that will read from the bronze table. We will also need to load a Delta Table external to our pipeline to validate records against it.

## Quarantine records

To capture all the records that failed the validation checks in the previous step, we will simply reverse the validation logic (e.g. person_id is expected to be null below) and load invalid records in a separate table.

## Conclusion

In this post, we covered a use case at Collective Health where our partners send us files at a given cadence. By leveraging the Databricks Data + AI Platform and Delta Live Tables, we are able to ingest files incrementally and also visualize and validate the quality of incoming records.

Learn more about the Databricks Data + AI Platform: [https://www.databricks.com/solutions/audience/digital-native](https://www.databricks.com/solutions/audience/digital-native)
