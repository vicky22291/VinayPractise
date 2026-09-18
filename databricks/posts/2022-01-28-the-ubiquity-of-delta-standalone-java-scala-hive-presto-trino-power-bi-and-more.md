# The Ubiquity of Delta Standalone: Java, Scala, Hive, Presto, Trino, Power BI, and More!

*Delta Standalone 0.3.0 ensures ACID transactions for the data engineering framework of your choice*

- Source: https://www.databricks.com/blog/2022/01/28/the-ubiquity-of-delta-standalone-java-scala-hive-presto-trino-power-bi-and-more.html
- Published: 2022-01-28
- Authors: Allison Portis, Scott Sandre, Denny Lee, Venki Korukanti, Shixiong Zhu
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

The Delta Standalone library is a single-node Java library that can be used to read from and write to Delta tables. Specifically, this library provides APIs to interact with a table's metadata in the transaction log, implementing the [Delta Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md) to achieve the transactional guarantees of the Delta Lake format. Notably, this project does not depend on Apache Spark™ and has only a few transitive dependencies. Therefore, it can be used by any processing engine or application to access Delta tables.

Delta Standalone is optimized for cases when you want to read and write Delta tables by using a non-Spark engine of your choice. It is a "low-level" library, and we encourage developers to contribute open-source, higher-level connectors for their desired engines that use Delta Standalone for all Delta Lake metadata interaction.

We are excited for the release of Delta Connectors 0.3.0, which introduces support for writing Delta tables. The key features in this release are:

**Delta Standalone**

-  
  - **Write functionality** - This release introduces new APIs to support creating and writing Delta tables without Apache Spark™. External processing engines can write Parquet data files and then use the APIs to commit the files to the Delta table atomically. Following the [Delta Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md), the implementation uses optimistic concurrency control to manage multiple writers, automatically generates checkpoint files, and manages log and checkpoint cleanup according to the protocol. The main Java class exposed is `OptimisticTransaction`, which is accessed via `DeltaLog.startTransaction()`.

 

-  
  - `OptimisticTransaction.markFilesAsRead(readPredicates)` must be used to read all metadata during the transaction (and not the `DeltaLog`. It is used to detect concurrent updates and determine if logical conflicts between this transaction and previously-committed transactions can be resolved.
  - `OptimisticTransaction.commit(actions, operation, engineInfo)` is used to commit changes to the table. If a conflicting transaction has been committed first (see above) an exception is thrown, otherwise, the table version that was committed is returned.
  - Idempotent writes can be implemented using `OptimisticTransaction.txnVersion(appId)` to check for version increases committed by the same application.
  - Each commit must specify the `Operation` being performed by the transaction.
  - Transactional guarantees for concurrent writes on Microsoft Azure and Amazon S3. This release includes custom extensions to support concurrent writes on Azure and S3 storage systems, which on their own do not have the necessary atomicity and durability guarantees. Please note that transactional guarantees are only provided for concurrent writes on S3 from a single cluster.
- **Memory-optimized iterator implementation for reading files in a snapshot**: `DeltaScan` introduces an iterator implementation for reading the `AddFiles` in a snapshot with support for partition pruning. It can be accessed via `Snapshot.scan()` or `Snapshot.scan(predicate)`, the latter of which filters files based on the `predicate` and any partition columns in the file metadata. This API significantly reduces the memory footprint when reading the files in a snapshot and instantiating a `DeltaLog` (due to internal utilization).
- **Partition filtering for metadata reads and conflict detection in writes**: This release introduces a simple expression framework for partition pruning in metadata queries. When reading files in a snapshot, filter the returned `AddFiles` on partition columns by passing a `predicate` into `Snapshot.scan(predicate)`. When updating a table during a transaction, specify which partitions were read by passing a `readPredicate` into `OptimisticTransaction.markFilesAsRead(readPredicate)` to detect logical conflicts and avoid transaction conflicts when possible.
-  
  - **Miscellaneous updates**:

 

-  
  - DeltaLog.getChanges() exposes an incremental metadata changes API. VersionLog wraps the version number and the list of actions in that version.
  - `ParquetSchemaConverter` converts a `StructType` schema to a Parquet schema.
  - Fix #197 for `RowRecord` so that values in partition columns can be read.
  - Miscellaneous bug fixes.

**Delta Connectors**

- **Hive 3 support for the** [Hive Connector](https://mvnrepository.com/artifact/io.delta/delta-hive)
- [Microsoft PowerBI](https://powerbi.microsoft.com/en-us/) **connector for reading Delta tables natively**: Read Delta tables directly from PowerBI from any storage supported system without running a Spark cluster. Features include online/scheduled refresh in the PowerBI service, support for Delta Lake time travel (e.g., `VERSION AS OF`), and partition elimination using the partition schema of the Delta table. For more details see the dedicated README.md.

## What is Delta Standalone?

The Delta Standalone project in Delta connectors, formerly known as Delta Standalone Reader (DSR), is a JVM library that can be used to read **and write** Delta Lake tables. Unlike [Delta Lake Core](https://github.com/delta-io/delta), this project does not use Spark to read or write tables and has only a few transitive dependencies. It can be used by any application that cannot use a Spark cluster (read more: [How to Natively Query Your Delta Lake with Scala, Java, and Python](https://www.databricks.com/blog/2020/12/22/natively-query-your-delta-lake-with-scala-java-and-python.html)).

The project allows developers to build a Delta connector for an external processing engine following the [Delta protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md#writer-version-requirements) *without using a* [*manifest file*](https://docs.delta.io/latest/presto-integration.html). The reader component ensures developers can read the set of parquet files associated with the Delta table version requested. As part of Delta Standalone 0.3.0, the reader includes a memory-optimized, lazy iterator implementation for `DeltaScan.getFiles` (PR #194). The following code sample reads Parquet files in a distributed manner where Delta Standalone (as of 0.3.0) includes `Snapshot::scan(filter)::getFiles`, which supports partition pruning and an optimized internal iterator implementation.

As well, Delta Standalone 0.3.0 includes a new writer component that allows developers to generate parquet files themselves and add these files to a Delta table atomically, with support for idempotent writes (read more: [Delta Standalone Writer design document](https://docs.google.com/document/d/1MJhmW_H7doGWY2oty-I78vciziPzBy_nzuuB-Wv5XQ8/edit#heading=h.j2yecuf2q7j4)). The following code snippet shows how to commit to the transaction log to add the new files and remove the old incorrect files after writing Parquet files to storage.

## Hive 3 using Delta Standalone

Delta Standalone 0.3.0 supports Hive 2 and 3 allowing Hive to natively read a Delta table. The following is an example of how to create a Hive external table to access your Delta table.

For more details on how to set up Hive, please refer to Delta Connectors > Hive Connector. It is important to note this connector only supports [Apache Hive](https://www.databricks.com/glossary/apache-hive); it does not support Apache Spark or Presto.

## Reading Delta Lake from PrestoDB

As demonstrated in [PrestoCon 2021](https://prestodb.io/prestocon_2021.html) session [Delta Lake Connector for Presto](https://www.youtube.com/watch?v=JrXGkqpl7xk), the recently merged [Presto/Delta connector](https://github.com/prestodb/presto/tree/master/presto-delta) utilizes the Delta Standalone project to natively read the Delta transaction log without the need of a manifest file. The memory-optimized, lazy iterator included in Delta Standalone 0.3.0 allows PrestoDB to efficiently iterate through the Delta transaction log metadata and avoids OOM issues when reading large Delta tables.

With the [Presto/Delta connector](https://github.com/prestodb/presto/tree/master/presto-delta), in addition to querying your Delta tables natively with Presto, you can use the `@` syntax to perform [time travel queries](https://www.databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html) and query previous versions of your Delta table by [version](https://github.com/prestodb/presto/blob/master/presto-delta/src/test/java/com/facebook/presto/delta/TestDeltaIntegration.java#L98) or [timestamp](https://github.com/prestodb/presto/blob/master/presto-delta/src/test/java/com/facebook/presto/delta/TestDeltaIntegration.java#L114). The following code sample is querying earlier versions of the same NYCTaxi 2019 dataset using version.

With this connector, you can both specify the table from your metastore and query the Delta table directly from the file path using the syntax of `deltas3."$path$"."s3://…`

For more information about the PrestoDB/Delta connector:

- [PrestoDB: Delta Lake Connector (docs)](https://github.com/prestodb/presto/blob/master/presto-docs/src/main/sphinx/connector/deltalake.rst)
- [Presto/Delta Connector source code](https://github.com/prestodb/presto/tree/master/presto-delta)

Note, we are currently working with the **Trino** (here’s the current branch that contains the [Trino 359 Delta Lake](https://github.com/vkorukanti/trino/tree/359-delta) reader) and **Athena** communities to provide native Delta Lake connectivity.

## Reading Delta Lake from Power BI Natively

We also wanted to give a shout-out to Gerhard Brueckl (github: [gbrueckl](https://github.com/gbrueckl)) for continuing to improve Power BI connectivity to Delta Lake. As part of Delta Connectors 0.3.0, the Power BI connector includes online/scheduled refresh in the PowerBI service, support for Delta Lake time travel, and partition elimination using the partition schema of the Delta table.

Source: [Reading Delta Lake Tables natively in PowerBI](https://blog.gbrueckl.at/2021/01/reading-delta-lake-tables-natively-in-powerbi/)

For more information, refer to [Reading Delta Lake Tables natively in PowerBI](https://blog.gbrueckl.at/2021/01/reading-delta-lake-tables-natively-in-powerbi/) or check out the code-base.

## Discussion

We are really excited about the rapid adoption of Delta Lake by the data engineering and data sciences community. If you’re interested in learning more about Delta Standalone or any of these Delta connectors, check out the following resources:

- Delta Integrations
- [Delta Users Slack](https://join.slack.com/t/delta-users/shared_invite/zt-ngdxlkxh-c~rjOonFCDS2xve_lx3TIA)
- [Delta Google Group](https://groups.google.com/forum/#!forum/delta-users)
- [Delta YouTube channel](https://www.youtube.com/c/deltalake), where we also host bi-weekly community office hours for Delta Core, Flink/Delta, Presto/Delta, and more!

---

**Credits**
We want to thank the following contributors for updates, doc changes, and contributions in Delta Standalone 0.3.0: Alex, Allison Portis, Denny Lee, Gerhard Brueckl, Pawel Kubit, Scott Sandre, Shixiong Zhu, Wang Wei, Yann Byron, Yuhong Chen, and gurunath.
