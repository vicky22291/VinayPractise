# Query Delta Lake Tables from Presto and Athena, Improved Operations Concurrency, and Merge performance

- Source: https://www.databricks.com/blog/2020/01/29/query-delta-lake-tables-presto-athena-improved-operations-concurrency-merge-performance.html
- Published: 2020-01-29
- Authors: Tathagata Das, Denny Lee
- Categories: solutions, engineering, open-source, data-engineering
- Images: 0 total, 0 extracted as architecture

[Get an early preview of O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=querydeltalakesprestoathena-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

---

 

We are excited to announce the release of Delta Lake 0.5.0, which introduces Presto/Athena support and improved concurrency.

**The key features in this release are:**

- **Support for other processing engines using manifest files** [(#76)](https://github.com/delta-io/delta/issues/76) - You can now query Delta tables from Presto and Amazon Athena using manifest files, which you can generate using Scala, Java, Python, and SQL APIs. See the Presto and Athena to Delta Lake Integration documentation for details
- **Improved concurrency for all Delta Lake operations** ([#9](https://github.com/delta-io/delta/issues/9), [#72](https://github.com/delta-io/delta/issues/72), [#228](https://github.com/delta-io/delta/issues/228)) - You can now run more Delta Lake operations concurrently. Delta Lake’s optimistic concurrency control has been improved by making conflict detection more fine-grained. This makes it easier to run complex workflows on Delta tables. For example:
  - Running deletes (e.g. for GDPR compliance) concurrently on older partitions while newer partitions are being appended.
  - Running updates and merges concurrently on disjoint sets of partitions.
  - Running file compactions concurrently with appends (see below).

For more information, please refer to the open-source Delta Lake 0.5.0 release notes. In this blog post, we will elaborate on reading Delta Lake tables with Presto, improved operations concurrency, easier and faster data deduplication using insert-only merge.

## Reading Delta Lake Tables with Presto

As described in [Simple, Reliable Upserts and Deletes on Delta Lake Tables using Python APIs](https://www.databricks.com/blog/2019/10/03/simple-reliable-upserts-and-deletes-on-delta-lake-tables-using-python-apis.html), modifications to the data such as deletes are performed by selectively writing new versions of the files containing the data be deleted and only marks the previous files as deleted. The advantage of this approach is that Delta Lake enables us to travel back in time (i.e. [time travel](https://www.databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html)) and query previous versions.

To understand which files (and rows) contain the latest data, by default you can query the transaction log (more information at [Diving Into Delta Lake: Unpacking The Transaction Log](https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html)). Other systems like Presto and Athena can read a generated manifest file - a text file containing the list of data files to read for querying a table. To do this, we will follow the Python instructions; for more information, refer to Set up the Presto or Athena to Delta Lake integration and query Delta tables.

## Generate Delta Lake Manifest File

Let’s start by creating the Delta Lake manifest file with the following code snippet.

As the name implies, this generates the manifest file in the table root folder. If you had created the departureDelays table per [Simple, Reliable Upserts and Deletes on Delta Lake Tables using Python APIs](https://www.databricks.com/blog/2019/10/03/simple-reliable-upserts-and-deletes-on-delta-lake-tables-using-python-apis.html), you will have a new folder in the table root folder:

with a single file named manifest. If you review the files within the manifest (e.g. cat manifest), you will get the following output indicating the files that contain the latest snapshot.

## Create Presto Table to Read Generated Manifest File

The next step is to create an external table in the Hive Metastore so that Presto (or Athena with Glue) can read the generated manifest file to identify which Parquet files to read for reading the latest snapshot of the Delta table. Note, for Presto, you can either use Apache Spark or the Hive CLI to run the following command. k.

Some important notes on schema enforcement:

- The schema defined on line 1 must match the schema of the Delta Lake table (e.g. in this example, `departureDelaysExternal`). Note, the partitioning scheme is optional.
- Line 5 points to the location of the manifest file in the form of `/_symlink_format_manifest/`

The SymlinkTextInputFormat configures Presto (or Athena) to get the list of Parquet data files from the manifest file instead of using directory listing. Note, for partitioned tables, there are additional steps that will need to be performed per Configure Presto to read the generated manifests.

### Update the Manifest File

It is important to note that every time the data is updated, you will need to regenerate the manifest file so Presto will be able to see the latest data.

## Improved Operations Concurrency

With the following pull requests, you can now run even more Delta Lake operations concurrently. With finer grain conflict detection, these updates make it easier to run complex workflows on Delta tables such as:

- Running deletes (e.g. for GDPR compliance) concurrently on older partitions while newer partitions are being appended.
- Running file compactions concurrently with appends.
- Running updates and merges concurrently on disjoint sets of partitions.

### Concurrent Appends Use Cases

For example, typically there is a ConcurrentAppendException thrown during concurrent merge operations when concurrent transaction adds records to the same partition.

The above code snippet potentially can cause conflicts because the condition is not explicit enough resulting even though the table is already partitioned by date and country. The issue is that the query currently will scan the entire table potentially resulting in a conflict with concurrent operations updating any other partitions. By specifying `specificDate` and `specificCountry` so you can merge on a specific date or country, this operation is now safe to run concurrently on different dates and countries.

This approach is the same for all other Delta Lake operations (e.g. delete, metadata changed, etc.).

### Concurrent File Compaction

If you are continuously writing data to a Delta table, over time a large number of files will be accumulated. This is especially important in streaming scenarios as you are adding data in small batches. This results in the file system continuing to accumulate many small files; this will degrade query performance over time. An important optimization task is to periodically take a large number of small files and rewrite them to a smaller number of larger files, i.e. file compaction.

In the past, there was a higher potential for an exception when concurrently querying the data and running file compaction. But, because of these improvements, you can also run queries (including streaming queries) and file compaction concurrently without any exceptions. For example, If your table is partitioned and you want to repartition just one partition based on a predicate, you can read only the partition using where and write back to that using `replaceWhere`:

Note, use the `dataChange == false` option only when there are no data changes (such as in the preceding code snippet) otherwise this may corrupt the underlying data.

## Easier and Faster Data Deduplication Using Insert-only Merge

A common [ETL](https://www.databricks.com/glossary/extract-transform-load) use case is to collect logs and append them into a Delta Lake table. A common issue is that the source generates duplicate log records. With Delta Lake merge, you can avoid inserting these duplicate records such as the following code snippet involving merging updated flight data.

Prior to Delta Lake 0.5.0, it was not possible to read deduped data as a stream from a Delta Lake table because insert-only merges were not pure appends into the table.

For example, in a streaming query, you can run a merge operation in `foreachBatch` to continuously write any streaming data into a Delta Lake table with deduplication as noted in the following [PySpark](https://www.databricks.com/glossary/pyspark) snippet.

In another streaming query, you can continuously read deduplicated data from this Delta Lake table. This is possible because insert-only merge - introduced in Delta Lake 0.5.0 - will only append new data to the Delta table.

## Getting Started with Delta Lake 0.5.0

Try out Delta Lake today by trying out the preceding code snippets on your Apache Spark 2.4.3 (or newer) instance. By using Delta Lake, you can make your data lakes more reliable (whether you create a new one or migrate an existing data lake). To learn more, refer to [https://delta.io/](https://delta.io/) and join the Delta Lake open source community via [Slack](https://delta-users.slack.com/join/shared_invite/enQtNTY1NDg0ODcxOTI1LWE3YjMxOTM4MmM0YWNhNjE2YmI2OGI4N2Y3MTRhOWQ1YzE3MTMyYTM5YzRiZWZlYzMwYzk0M2JiZmJhY2Q4NWI) and [Google Group](https://groups.google.com/forum/#!forum/delta-users). You can track all the upcoming releases and planned features in [Delta Lake github milestones](https://github.com/delta-io/delta/milestones).

## Credits

We want to thank the following contributors for updates, doc changes, and contributions in Delta Lake 0.5.0: Andreas Neumann, Andrew Fogarty, Burak Yavuz, Denny Lee, Fabio B. Silva, JassAbidi, Matthew Powers, Mukul Murthy, Nicolas Paris, Pranav Anand, Rahul Mahadev, Reynold Xin, Shixiong Zhu, Tathagata Das, Tomas Bartalos, and Xiao Li.
