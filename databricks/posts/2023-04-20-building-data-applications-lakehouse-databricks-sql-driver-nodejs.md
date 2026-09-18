# Building Data Applications on the Lakehouse With the Databricks SQL Driver for Node.js

- Source: https://www.databricks.com/blog/2023/04/20/building-data-applications-lakehouse-databricks-sql-driver-nodejs.html
- Published: 2023-04-20
- Authors: Andre Furlan Bueno, Can Efeoglu, Levko Kravets, Nithin Krishnamurthi
- Categories: platform, product, data-warehousing
- Images: 0 total, 0 extracted as architecture

We are excited to announce the general availability of the [Databricks SQL Driver for NodeJS](https://docs.databricks.com/dev-tools/nodejs-sql-driver.html). This follows the recent general availability of [Databricks SQL Driver for GO](https://docs.databricks.com/dev-tools/go-sql-driver.html) and the earlier [Databricks SQL Connector for Python](https://docs.databricks.com/dev-tools/python-sql-connector.html). Node.js developers can now easily build data applications on the lakehouse in pure Javascript or TypeScript.

The NodeJS driver offers simple installation and a flexible interface that makes it easy to query data. It also automatically converts data types between Databricks SQL and Node.js clients, removing the need for boilerplate code.

This blog post will use examples of connecting to Databricks and running queries against a sample data set.

## Simple installation from npm

With this Node.js driver, there's no need to deal with ODBC/JDBC driver dependencies. Installation is through npm, which means you can include this connector in your application and use it for CI/CD. On NodeJS 14 or newer:

## Setting up connection

The connector works with SQL warehouses and All Purpose Clusters. This example shows you how to connect to and run a query on a SQL Warehouse. We import the connector and pass in [connection and authentication information](https://docs.databricks.com/integrations/bi/jdbc-odbc-bi.html#get-server-hostname-port-http-path-and-jdbc-url) to establish a connection. You can authenticate using a Databricks personal access token (PAT) or a Microsoft Azure active directory (AAD) token (to be released shortly).

## Querying data

The following example retrieves a list of trips from the NYC taxi sample dataset and prints the result to the console.

Our [documentation](https://docs.databricks.com/dev-tools/nodejs-sql-driver.html#query-data) includes examples in Javascript and TypeScript to help you get started, as well as the full API reference.

## A bright future for Node.js developers on the lakehouse

We're happy to announce that our Node.js driver is open source on [Github](https://github.com/databricks/databricks-sql-nodejs). We welcome contributions from the community. We're already seeing our partners, such as [Qlik Analytics](https://www.qlik.com/us/), use the Node connector in their products.

We're even more excited about what our customers will build with the Databricks SQL Driver for Node.js! Please try out the driver and let us know your thoughts on Github. We would love to hear what you would like us to support.
