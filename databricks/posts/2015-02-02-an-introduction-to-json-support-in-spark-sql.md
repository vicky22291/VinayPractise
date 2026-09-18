# An introduction to JSON support in Spark SQL

- Source: https://www.databricks.com/blog/2015/02/02/an-introduction-to-json-support-in-spark-sql.html
- Published: 2015-02-02
- Authors: Yin Huai
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

Check out the [Why the Data Lakehouse is Your Next Data Warehouse](https://www.databricks.com/resources/ebook/bring-data-warehousing-data-lakes?itm_data=jsonsupportspark-blog-whylakehouseisnextdw ) ebook to discover the inner workings of the Databricks Lakehouse Platform.

 

*Note: Starting Spark 1.3, SchemaRDD will be renamed to DataFrame.*

---

In this blog post, we introduce Spark SQL’s JSON support, a feature we have been working on at Databricks to make it dramatically easier to query and create JSON data in Spark. With the prevalence of web and mobile applications, JSON has become the de-facto interchange format for web service API’s as well as long-term storage. With existing tools, users often engineer complex pipelines to read and write JSON data sets within analytical systems. Spark SQL’s JSON support, released in Apache Spark 1.1 and enhanced in Apache Spark 1.2, vastly simplifies the end-to-end-experience of working with JSON data.

## Existing practices

In practice, users often face difficulty in manipulating JSON data with modern analytical systems. To write a dataset to JSON format, users first need to write logic to convert their data to JSON. To read and query JSON datasets, a common practice is to use an ETL pipeline to transform JSON records to a pre-defined structure. In this case, users have to wait for this process to finish before they can consume their data. For both writing and reading, defining and maintaining schema definitions often make the ETL task more onerous, and eliminate many of the benefits of the semi-structured JSON format. If users want to consume fresh data, they either have to laboriously define the schema when they create external tables and then use a custom JSON serialization/deserialization library, or use a combination of JSON UDFs to query the data.

As an example, consider a dataset with following JSON schema:

In a system like Hive, the JSON objects are typically stored as values of a single column. To access this data, fields in JSON objects are extracted and flattened using a UDF. In the SQL query shown below, the outer fields (name and address) are extracted and then the nested address field is further extracted.

*In the following example it is assumed that the JSON dataset shown above is stored in a table called people and JSON objects are stored in the column called jsonObject.*

## JSON support in Spark SQL

Spark SQL provides a natural syntax for querying JSON data along with automatic inference of JSON schemas for both reading and writing data. Spark SQL understands the nested fields in JSON data and allows users to directly access these fields without any explicit transformations. The above query in Spark SQL is written as follows:

### Loading and saving JSON datasets in Spark SQL

To query a JSON dataset in Spark SQL, one only needs to point Spark SQL to the location of the data. The schema of the dataset is inferred and natively available without any user specification. In the programmatic APIs, it can be done through jsonFile and jsonRDD methods provided by SQLContext. With these two methods, you can create a SchemaRDD for a given JSON dataset and then you can register the SchemaRDD as a table. Here is an example:

It is also possible to create a JSON dataset using a purely SQL API. For instance, for those connecting to Spark SQL via a JDBC server, they can use:

In the above examples, because a schema is not provided, Spark SQL will automatically infer the schema by scanning the JSON dataset. When a field is JSON object or array, Spark SQL will use STRUCT type and ARRAY type to represent the type of this field. Since JSON is semi-structured and different elements might have different schemas, Spark SQL will also resolve conflicts on data types of a field. To understand what is the schema of the JSON dataset, users can visualize the schema by using the method of printSchema() provided by the returned SchemaRDD in the programmatic APIs or by using DESCRIBE [table name] in SQL. For example, the schema of people visualized through people.printSchema() will be:

Optionally, a user can apply a schema to a JSON dataset when creating the table using jsonFile and jsonRDD. In this case, Spark SQL will bind the provided schema to the JSON dataset and will not infer the schema. Users are not required to know all fields appearing in the JSON dataset. The specified schema can either be a subset of the fields appearing in the dataset or can have field that does not exist.

After creating the table representing a JSON dataset, users can easily write SQL queries on the JSON dataset just as they would on regular tables. As with all queries in Spark SQL, the result of a query is represented by another SchemaRDD. For example:

The result of a SQL query can be used directly and immediately by other data analytic tasks, for example a machine learning pipeline. Also, JSON datasets can be easily cached in Spark SQL’s built in in-memory columnar store and be save in other formats such as Parquet or Avro.

### Saving SchemaRDDs as JSON files

In Spark SQL, SchemaRDDs can be output in JSON format through the toJSON method. Because a SchemaRDD always contains a schema (including support for nested and complex types), Spark SQL can automatically convert the dataset to JSON without any need for user-defined formatting. SchemaRDDs can themselves be created from many types of data sources, including [Apache Hive](https://www.databricks.com/glossary/apache-hive) tables, Parquet files, JDBC, Avro file, or as the result of queries on existing SchemaRDDs. This combination means users can migrate data into JSON format with minimal effort, regardless of the origin of the data source.

## What's next?

There are also several features in the pipeline that with further improve Spark SQL's support for semi-structured JSON data.

### Improved SQL API support to read/write JSON datasets

In Apache Spark 1.3, we will introduce improved JSON support based on the new data source API for reading and writing various format using SQL. Users can create a table from a JSON dataset with an optional defined schema like what they can do with jsonFile and jsonRDD. Also, users can create a table and ask Spark SQL to store its rows in JSON objects. Data can inserted into this table through SQL. Finally, a CREATE TABLE AS SELECT statement can be used to create such a table and populate its data.

### Handling JSON datasets with a large number of fields

JSON data is often semi-structured, not always following a fixed schema. In the future, we will expand Spark SQL’s JSON support to handle the case where each object in the dataset might have considerably different schema. For example, consider a dataset where JSON fields are used to hold key/value pairs representing HTTP headers. Each record might introduce new types of headers and using a distinct column for each one would produce a very wide schema. We plan to support auto-detecting this case and instead use a Map type. Thus, each row may contain a Map, enabling querying its key/value pairs. This way, Spark SQL will handle JSON datasets that have much less structure, pushing the boundary for the kind of queries SQL-based systems can handle.

*To try out these new Spark features, [get a free trial of Databricks or use the Community Edition](https://www.databricks.com/try-databricks).*
