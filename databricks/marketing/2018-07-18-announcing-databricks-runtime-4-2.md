# Announcing Databricks Runtime 4.2!

- Source: https://www.databricks.com/blog/2018/07/18/announcing-databricks-runtime-4-2.html
- Published: 2018-07-18
- Authors: Todd Greenstein
- Categories: company, product, engineering, data-engineering, announcements, customers, platform, open-source
- Images: 0 total, 0 extracted as architecture

We’re excited to announce Databricks Runtime 4.2, powered by Apache Spark™.  Version 4.2 includes updated Spark internals, new features, and major performance upgrades to Databricks Delta, as well as general quality improvements to the platform.  We are moving quickly toward the Databricks Delta general availability (GA) release and we recommend you upgrade to Databricks Runtime 4.2 to take advantage of these improvements.

I'd like to take a moment to highlight some of the work the team has done to continually improve Databricks Delta:

- **Streaming Directly to Delta Tables:** Streams can now be directly written to a Databricks Delta table registered in the Hive metastore using df.writeStream.table(...).
- **Path Consistency for Delta Commands:** All Databricks Delta commands and queries now support referring to a table using its path as an identifier (that is, delta.`/path/to/table`). Previously OPTIMIZE and VACUUM required non-standard use of string literals (that is, '/path/to/table').

We've also included powerful new features to Structured Streaming:

- **Robust Streaming Pipelines with Trigger.Once:** is now supported in Databricks Delta.   Rate limits (for example maxOffsetsPerTrigger or maxFilesPerTrigger) specified as source options or defaults could result in partial execution of available data. These options are now ignored when Trigger.Once is used, allowing all currently available data to be processed.  Documentation is available at: [Trigger.Once](https://docs.databricks.com/release-notes/runtime/4.2.html#id1) in the Databricks Runtime 4.2 release notes.
- **Flexible Streaming Sink to Many Storage Options with foreachBatch():** You can now define a function to process the output of every microbatch using DataFrame operations in Scala.  Documentation is available at: [foreachBatch()](https://docs.databricks.com/spark/latest/structured-streaming/foreach.html#reuse-existing-batch-data-sources-with-foreachbatch). This can help in new ways of flexibility but most importantly, foreachBatch() can let you write to a range of storage options even if they don’t support streaming as a sink.
- **Support for streaming foreach() in Python has also been added. **Documentation is available at: [foreach().](https://docs.databricks.com/spark/latest/structured-streaming/foreach.html#using-python)

We included support for the **SQL Deny** **command** for table access control enabled clusters. Users can now deny specific permissions in the same way they are granted. A denied permission will supersede a granted one.  Detailed technical documentation is available at: [SQL DENY](https://docs.databricks.com/security/access-control/table-acls/object-privileges.html#deny).

To read more about the above new features and to see the full list of improvements included in Databricks Runtime 4.2, please refer to the release notes in the following locations:

- Amazon Web Services: [Databricks Runtime 4.2 release notes](https://docs.databricks.com/release-notes/runtime/4.2.html)
- Azure: :[Databricks Runtime 4.2 release notes](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/4.2#other-changes-and-improvements)
