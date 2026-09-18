# Building Data Applications on the Lakehouse With the Databricks SQL Driver for GO

- Source: https://www.databricks.com/blog/2023/04/20/building-data-applications-lakehouse-databricks-sql-driver-go.html
- Published: 2023-04-20
- Authors: Andre Furlan Bueno, Raymond Cypher, Can Efeoglu, Matthew Kim
- Categories: platform, product, data-warehousing
- Images: 0 total, 0 extracted as architecture

We are excited to announce the general availability of the [Databricks SQL Driver for GO](https://docs.databricks.com/dev-tools/go-sql-driver.html). This follows the recent general availability of [Databricks SQL Driver for NodeJS](https://docs.databricks.com/dev-tools/nodejs-sql-driver.html) and the earlier [Databricks SQL Connector for Python](https://docs.databricks.com/dev-tools/python-sql-connector.html). GO developers can now easily build data applications on the lakehouse in GO.

By providing a native driver in pure GO compliant with the [database/sql](https://golang.org/pkg/database/sql) package, we enable a simple developer experience that API developers already know. These apps can benefit from Go's speed as a compiled language to fetch larger amounts of data.

In this blog post, we will run through some examples of connecting to Databricks and running queries against a sample dataset.

## Simple package import

With this GO driver, there's no need to deal with ODBC/JDBC driver dependencies. To get started, simply import [database/sql](https://golang.org/pkg/database/sql) and Databricks SQL Driver fo GO as follows:

## Setting up connection

The connector works with SQL Warehouses as well as All Purpose Clusters. In this example, we show you how to connect to and run a query on a SQL Warehouse. To establish a connection, we import the connector and pass in [connection and authentication information](https://docs.databricks.com/integrations/bi/jdbc-odbc-bi.html#get-server-hostname-port-http-path-and-jdbc-url). You can authenticate using a Databricks personal access token (PAT) or a Microsoft Azure active directory (AAD) token.

## Querying data

The following example retrieves a list of trips from the NYC taxi sample dataset and prints trip distances the result to the console.

Check our [documentation](https://docs.databricks.com/dev-tools/go-sql-driver.html) for more examples & full API reference.

## A bright future for Go developers on the lakehouse

We're happy to announce that our GO driver is open source on [Github](https://github.com/databricks/databricks-sql-go). We welcome contributions from the community. We're pleased to have worked with several partners while developing this driver, especially [Sigma](https://www.sigmacomputing.com/) who are using this new driver to bring their powerful BI and analytics capabilities to Databricks customers.

We're even more excited about what our customers will build with the Databricks SQL Driver for GO! Please try out the driver and let us know what you think on Github. We would love to hear from you on what you would like us to support.
