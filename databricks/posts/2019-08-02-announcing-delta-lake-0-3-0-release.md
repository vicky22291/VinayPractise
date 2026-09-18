# Announcing the Delta Lake 0.3.0 Release

- Source: https://www.databricks.com/blog/2019/08/02/announcing-delta-lake-0-3-0-release.html
- Published: 2019-08-02
- Authors: Tathagata Das, Rahul Mahadev, Zhitong Yan, Prakash Chockalingam
- Categories: platform, engineering
- Images: 0 total, 0 extracted as architecture

[Get an early preview of O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=deltalake030release-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

---

We are excited to announce the [release](https://github.com/delta-io/delta/releases/tag/v0.3.0) of Delta Lake 0.3.0 which introduces new programmatic APIs for manipulating and managing data in Delta tables. The key features in this release are:

- **Scala/Java APIs for DML commands -** You can now modify data in Delta tables using programmatic APIs for Delete ([#44](https://github.com/delta-io/delta/issues/44)), Update ([#43](https://github.com/delta-io/delta/issues/43)) and Merge ([#42](https://github.com/delta-io/delta/issues/42)). These APIs mirror the syntax and semantics of their corresponding SQL commands and are great for many workloads, e.g., Slowly Changing Dimension (SCD) operations, merging change data for replication, and upserts from streaming queries. See the documentation for more details.
- **Scala/Java APIs for query commit history **([#54](https://github.com/delta-io/delta/issues/54)) - You can now query a table’s commit history to see what operations modified the table. This enables you to audit data changes, time travel queries on specific versions, debug and recover data from accidental deletions, etc. See the documentation for more details.
- **Scala/Java APIs for vacuuming old files** [#48](https://github.com/delta-io/delta/issues/48) - Stale snapshots (as well as other uncommitted files from aborted transactions) can be garbage collected by vacuuming the table. See the documentation for more details.

## Updates and Deletes

There are a number of common use cases where existing data in a [data lake](https://www.databricks.com/discover/data-lakes/introduction) needs to be updated or deleted:

- General Data Protection Regulation (GDPR) and California Consumer Privacy Act (CCPA) compliance
- Change data capture from traditional databases
- Sessionization to group multiple events into a single session is a common use case in many areas ranging from product analytics to targeted advertising to predictive maintenance.
- Deduplication of records from sources

Since data lakes are fundamentally based on files, they have always been optimized for appending data than for changing existing data. Hence, building the above use case has always been challenging. Users typically read the entire table (or a subset of partitions) and then overwrite them. Therefore, every organization tries to reinvent the wheel for their requirement by hand-writing complicated queries in SQL, Spark, etc.

One of the popular demands in Delta Lake is support for updates and deletes. In 0.3.0 release, we have added Scala / Java APIs to easily merge and delete records.

### Delete Example

You can remove data that matches a predicate from a Delta Lake table. For instance, to delete all events from before 2017, you can run the following:

### Update Example

You can update data that matches a predicate in a Delta Lake table. For example, to fix a spelling mistake in the `eventType`, you can run the following:

### Merge Example

You can upsert data from a Spark DataFrame into a Delta Lake table using the merge operation. This operation is similar to the SQL MERGE command but has additional support for deletes and extra conditions in updates, inserts, and deletes.

Suppose you have a Spark DataFrame that contains new data for events with eventId. Some of these events may already be present in the events table. So when you want to merge the new data into the events table, you want to update the matching rows (that is, eventId already present) and insert the new rows (that is, eventId no present). You can run the following:

See Programmatic API Docs to understand more details on the APIs.

## Query Commit History

Delta Lake automatically versions the data that you store. Delta Lake maintains a commit history about all the operations that modified the table. With this release, you can now access the commit history of the table and understand what operations modified the table.

Auditing data changes is critical from both in terms of data compliance as well as simple debugging to understand how data has changed over time. Organizations moving from traditional data systems to big data technologies and the cloud struggle in such scenarios. The new API would allow users to maintain a track of all the changes to a table.

You can retrieve information on the operations, user, timestamp, and so on for each write to a Delta Lake table by running the history command. The operations are returned in reverse chronological order. By default, table history is retained for 30 days.

The returned DataFrame will have the following structure.

## Vacuum

Delta Lake uses [MVCC](https://en.wikipedia.org/wiki/Multiversion_concurrency_control) to enable snapshot isolation and time travel. However, keeping all versions of a table forever can be prohibitively expensive. You can remove files that are older than the retention threshold by running vacuum on the table. The default retention threshold for the files is 7 days. The ability to time travel back to a version older than the retention period is lost after running vacuum. Running the vacuum command on the table recursively vacuums the directories associated with the Delta Lake table.

## Cloud Storage Support

In case you missed it, in our earlier [0.2.0 release](https://github.com/delta-io/delta/releases/tag/v0.2.0), we added support for cloud stores like S3 and Azure blob store. The release also includes support for improved concurrency. If you are running big data workloads in the cloud, check out our previous release.

## What’s Next

We are already gearing up for our next release in September. The major features we are currently working on is the python and SQL APIs for Delta DMLs and data expectations which will allow you to set validations on your tables. You can track all the upcoming releases and planned features in [github milestones](https://github.com/delta-io/delta/milestones).

Coming up, we’re also excited to have [Spark AI Summit Europe](https://www.databricks.com/sparkaisummit/europe) from October 15th to 17th. At the summit, we’ll have a [training session dedicated to Delta Lake](https://www.databricks.com/sparkaisummit/europe#building-data-pipelines). Early bird registration ends on August 16th 2019.
