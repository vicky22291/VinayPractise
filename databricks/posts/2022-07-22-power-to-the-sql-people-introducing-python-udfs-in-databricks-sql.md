# Power to the SQL People: Introducing Python UDFs in Databricks SQL

- Source: https://www.databricks.com/blog/2022/07/22/power-to-the-sql-people-introducing-python-udfs-in-databricks-sql.html
- Published: 2022-07-22
- Authors: Martin Grund, Herman van Hövell, Stefania Leone, Jakob Mund
- Categories: platform, announcements, data-warehousing
- Images: 0 total, 0 extracted as architecture

We were thrilled to announce the preview for Python User-Defined Functions (UDFs) in Databricks SQL (DBSQL) at last month's Data and AI Summit. This blog post gives an overview of the new capability and walks you through an example showcasing its features and use-cases.

Python UDFs allow users to write Python code and invoke it through a SQL function in an easy secure and fully governed way, bringing the power of Python to Databricks SQL.

## Introducing Python UDFs to Databricks SQL

In Databricks and Apache Spark™ in general, UDFs are means to extend Spark: as a user, you can define your business logic as reusable functions that extend the vocabulary of Spark, e.g. for transforming or masking data and reuse it across their applications. With Python UDFs for Databricks SQL, we will expand our current support for [SQL UDFs](https://www.databricks.com/blog/2021/10/20/introducing-sql-user-defined-functions.html).

Let's look at a Python UDF example. Below the function redacts email and phone information from a JSON string, and returns the redacted string, e.g., to prevent unauthorized access to sensitive data:

To define the Python UDF, all you have to do is a `CREATE FUNCTION` SQL statement. This statement defines a function name, input parameters and types, specifies the language as `PYTHON`, and provides the function body between $$.

The function body of a Python UDF in Databricks SQL is equivalent to a regular Python function, with the UDF itself returning the computation's final value. Dependencies from the Python standard library and [Databricks Runtime 10.4](https://docs.databricks.com/release-notes/runtime/10.4.html#system-environment), such as the json package in the above example, can be imported and used in your code. You can also define nested functions inside your UDF to encapsulate code to build or reuse complex logic.

From that point on, all users with appropriate permissions can call this function as you do for any other built-in function, e.g., in the `SELECT`, `JOIN` or `WHERE` part of a query.

## Features of Python UDFs in Databricks SQL

Now that we described how easy it is to define Python UDFs in Databricks SQL, let's look at how it can be managed and used within Databricks SQL and across the lakehouse.

### Manage and govern Python UDFs across all workspaces

Python UDFs are defined and managed as part of [Unity Catalog](https://www.databricks.com/product/unity-catalog), providing strong and fine-grained management and governance means:

- Python UDFs permissions can be controlled on a group (recommended) or user level across all workspaces using GRANT and REVOKE statements.
- To create a Python UDF, users need USAGE and CREATE permission on the schema and USAGE permission on the catalog. To run a UDF, users need EXECUTE on the UDF. For instance, to grant the *finance-analysts* group permissions to use the above `redact` Python UDF in their SQL expressions, issue the following statement:

- Members of the finance-analyst group can use the redact UDF in their SQL expressions, as shown below, where the contact_info column will contain no phone or email addresses.

### Enterprise-grade security and multi-tenancy

With the great power of Python comes great responsibility. To ensure Databricks SQL and Python UDFs meet the strict requirements for enterprise security and scale, we took extra precautions to ensure it meets your needs.

To this end, compute and data are fully protected from the execution of Python code within your Databricks SQL warehouse. Python code is executed in a secure environment preventing:

- Access to data not provided as parameters to the UDF, including file system or memory outside of the Python execution environment
- Communication with external services, including the network, disk or inter-process communication

This execution model is built from the ground up to support the concurrent execution of queries from multiple users leveraging additional computation in Python without sacrificing any security requirements.

### Do more with less using Python UDFs

Serving as an extensibility mechanism there are plenty of use-cases for implementing custom business logic with Python UDFs.

Python is a great fit for writing complex parsing and data transformation logic which requires customization beyond what's available in SQL. This can be the case if you are looking at very specific or proprietary ways to protect data. Using Python UDFs, you can implement custom tokenization, data masking, data redaction, or encryption mechanisms.

Python UDFs are also great if you want to extend your data with advanced computations or even ML model predictions. Examples include advanced geo-spatial functionality not available out-of-the-box and numerical or statistical computations, e.g., by building upon NumPy or pandas.

### Re-use existing code and powerful libraries

If you have already written Python functions across your data and analytics stack you can now easily bring this code into Databricks SQL with Python UDFs. This allows you to double-dip on your investments and onboard new workloads faster in Databricks SQL.

Similarly, having access to all packages of Python's standard library and the Databricks Runtime allows you to build your functionality on top of those libraries, supporting high quality of your code while at the same time making more efficient use of your time.

## Get started with Python UDFs on Databricks SQL and the Lakehouse

If you already are a Databricks customer, [sign up for the private preview](https://dbricks.co/udfpreview) today. We'll provide you with all the necessary information and documentation to get you started as part of the private preview.

If you want to learn more about Unity Catalog, [check out this website](https://www.databricks.com/product/unity-catalog). If you are not a Databricks customer, [sign up for a free trial](https://www.databricks.com/try-databricks) and start exploring the endless possibilities of Python UDFs, Databricks SQL and the Databricks Lakehouse Platform.

Join the conversation and share your ideas and use-cases for Python UDFs in the [Databricks Community](https://community.databricks.com/s/topic/0TO8Y000000VJEhWAO/summit22?_gl=1*1siibyk*_gcl_aw*R0NMLjE2NTU0NjcwNDkuQ2owS0NRand6TENWQmhEM0FSSXNBUEtZVGNRUVRTZ2s0N1BzQWYxSUJKalZkbTJHNGZBRzBNRFYwRUJXMjRGcERIYnpnUHhXbThsMmdDVWFBclNwRUFMd193Y0I.*_ga*MTExODA5NTM0OS4xNjUxNDg4ODU5*_ga_PQSEQ3RZQC*MTY1NzA5MTE2OC4zNi4xLjE2NTcwOTE1OTUuMA..&_ga=2.258861002.1184641463.1656934489-1118095349.1651488859&_gac=1.215429477.1655467050.Cj0KCQjwzLCVBhD3ARIsAPKYTcQQTSgk47PsAf1IBJjVdm2G4fAG0MDV0EBW24FpDHbzgPxWm8l2gCUaArSpEALw_wcB) where data-obsessed peers are chatting about Data + AI Summit 2022 announcements and updates. Learn. Network. Celebrate.
