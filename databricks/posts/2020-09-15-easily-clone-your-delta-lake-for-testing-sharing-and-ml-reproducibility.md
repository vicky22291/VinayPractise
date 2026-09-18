# Easily Clone your Delta Lake for Testing, Sharing, and ML Reproducibility

- Source: https://www.databricks.com/blog/2020/09/15/easily-clone-your-delta-lake-for-testing-sharing-and-ml-reproducibility.html
- Published: 2020-09-15
- Authors: Burak Yavuz, Pranav Anand
- Categories: engineering, databricks-ai
- Images: 1 total, 0 extracted as architecture

## Introducing Clones

**An efficient way to make copies of large datasets for testing, sharing and reproducing ML experiments **

We are excited to introduce a new capability in Databricks Delta Lake - *table cloning*. Creating copies of tables in a data lake or data warehouse has several practical uses. However, given the volume of data in tables in a data lake and the rate of its growth, making physical copies of tables is an expensive operation. Databricks Delta Lake now makes the process simpler and cost-effective with the help of table clones.

 Get an early preview of [O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=clonedlreproducibility-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

## What are clones anyway?

Clones are replicas of a source table at a given point in time. They have the same metadata as the source table: same schema, constraints, column descriptions, statistics, and partitioning. However, they behave as a separate table with a separate lineage or history. Any changes made to clones only affect the clone and not the source. Any changes that happen to the source during or after the cloning process also do not get reflected in the clone due to Snapshot Isolation. In Databricks Delta Lake we have two types of clones: *shallow* or *deep*.

### Shallow Clones

A *shallow* (also known as Zero-Copy) clone only duplicates the metadata of the table being cloned; the data files of the table itself are not copied. This type of cloning does not create another physical copy of the data resulting in minimal storage costs. Shallow clones are inexpensive and can be extremely fast to create. These clones are **not self-contained** and **depend on the source from which they were cloned as the source of data**. If the files in the source that the clone depends on are removed, for example with VACUUM, a shallow clone may become unusable. Therefore, shallow clones are typically used for short-lived use cases such as testing and experimentation.

### Deep Clones

Shallow clones are great for short-lived use cases, but some scenarios require a separate and independent copy of the table’s data. A *deep* clone makes a full copy of the  metadata *and* data files of the table being cloned. In that sense it is similar in functionality to copying with a CTAS command (CREATE TABLE.. AS… SELECT...). But it is simpler to specify since it makes a faithful copy of the original table at the specified version and you don’t need to re-specify partitioning, constraints and other information as you have to do with CTAS. In addition, it is much **faster**, **robust**, and can work in an **incremental** manner against failures!

With deep clones, we copy additional  metadata, such as your streaming application transactions and COPY INTO transactions, so you can continue your ETL applications exactly where it left off on a deep clone!

## Where do clones help?

Sometimes I wish I had a clone to help with my chores or magic tricks. However, we’re not talking about human clones here. There are many scenarios where you need a copy of your datasets - for exploring, sharing, or testing ML models or analytical queries. Below are some example customer use cases.

### Testing and experimentation with a production table

When users need to test a new version of their data pipeline they often have to rely on sample test datasets which are not representative of all the data in their production environment. Data teams may also want to experiment with various indexing techniques to improve performance of queries against massive tables. These experiments and tests cannot be carried out in a production environment without risking production data processes and affecting users.

It can take many hours or even days, to spin up copies of your production tables for a test or a development environment. Add to that, the extra storage costs for your development environment to hold all the duplicated data - there is a large overhead in setting a test environment reflective of the production data. With a shallow clone, this is trivial:

After creating a shallow clone of your table in a matter of seconds, you can start running a copy of your pipeline to test out your new code, or try optimizing your table in different dimensions to see how you can improve your query performance, and much much more. These changes will only affect your shallow clone, not your original table.

### Staging major changes to a production table

Sometimes, you may need to perform some major changes to your production table. These changes may consist of many steps, and you don’t want other users to see the changes which you’re making until you’re done with all of your work. A shallow clone can help you out here:

Once you’re happy with the results, you have two options. If no other change has been made to your source table, you can replace your source table with the clone. If changes have been made to your source table, you can merge the changes into your source table.

### Machine Learning result reproducibility

Coming up with an effective ML model is an iterative process. Throughout this process of tweaking the different parts of the model data scientists need to assess the accuracy of the model against a fixed dataset. This is hard to do in a system where the data is constantly being loaded or updated. A snapshot of the data used to train and test the model is required. This snapshot allows the results of the ML model to be reproducible for testing or model governance purposes. We recommend leveraging [Time Travel](https://www.databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html) to run multiple experiments across a snapshot; an example of this in action can be seen in [Machine Learning Data Lineage with MLflow and Delta Lake](https://www.databricks.com/session_na20/machine-learning-data-lineage-with-mlflow-and-delta-lake). Once you’re happy with the results and would like to archive the data for later retrieval, for example next Black Friday, you can use deep clones to simplify the archiving process. MLflow integrates really well with Delta Lake, and the auto logging feature `(mlflow.spark.autolog() )` will tell you, which version of the table was used to run a set of experiments.

## Data Migration

A massive table may need to be moved to a new, dedicated bucket or storage system for performance or governance reasons. The original table will not receive new updates going forward and will be deactivated and removed at a future point in time. Deep clones make the copying of massive tables more robust and scalable.

With deep clones, since we copy your **streaming application transactions** and **COPY INTO transactions**, you can continue your ETL applications from **exactly where it left off** after this migration!

## Data Sharing

In an organization it is often the case that users from different departments are looking for data sets that they can use to enrich their analysis or models. You may want to share your data with other users across the organization. But rather than setting up elaborate pipelines to move the data to yet another store it is often easier and economical to create  a copy of the relevant data set for users to explore and test the data to see if it is a fit for their needs without affecting your own production systems. Here deep clones again come to the rescue.

## Data Archiving

For regulatory or archiving purposes all data in a table needs to be preserved for a certain number of years, while the active table retains data for a few months. If you want your data to be updated as soon as possible, but however you have a requirement to keep data for several years, storing this data in a single table and performing time travel may become prohibitively expensive. In this case, archiving your data in a daily, weekly or monthly manner is a better solution. The incremental cloning capability of deep clones will really help you here.

Note that this table will have an independent history compared to the source table, therefore time travel queries on the source table and the clone may return different results based on your frequency of archiving.

## Looks awesome! Any gotchas?

Just to reiterate some of the gotchas mentioned above as a single list, here’s what you should be wary of:

- Clones are executed on a snapshot of your data. Any changes that are made to the source table after the cloning process starts **will not be reflected** in the clone.
- **Shallow clones are not self-contained** tables like deep clones. If the data is deleted in the source table (for example through VACUUM), your shallow clone may not be usable.
- Clones have a **separate, independent history** from the source table. Time travel queries on your source table and clone may not return the same result.
- Shallow clones **do not copy** stream transactions or COPY INTO metadata. Use deep clones to migrate your tables and continue your ETL processes from where it left off.

## How can I use it?

Shallow and Deep clones support new advances in how data teams test and manage their modern cloud data lakes and warehouses. Table clones can help your team now implement production-level testing of their pipelines, fine tune their indexing for optimal query performance, create table copies for sharing - all with minimal overhead and expense. If this is a need in your organization we hope you will take table cloning for a spin and give us your feedback - we look forward to hearing about new use cases and extensions you would like to see in the future.

The feature is available in Databricks 7.2 as a public preview for all customers. [Learn more](https://docs.databricks.com/delta/delta-utility.html#clone-a-delta-table) about the feature. To see it in action, [sign up for a free trial](https://www.databricks.com/try-databricks) of Databricks.
