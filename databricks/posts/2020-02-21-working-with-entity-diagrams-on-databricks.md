# Working with Entity Relationship (ER) Diagrams on Databricks

- Source: https://www.databricks.com/blog/2020/02/21/working-with-entity-diagrams-on-databricks.html
- Published: 2020-02-21
- Authors: Greg Rahn
- Categories: platform, engineering
- Images: 4 total, 0 extracted as architecture

## Introduction

Databricks supports the standard SQL data types and has first-class support for both ODBC and JDBC clients.  This means that most 3rd party SQL tools will work with Databricks.  In this article, we’ll dive into connecting one of these tools to Databricks with the focus on generating an Entity-Relationship (ER) Diagram.

## Setup

### Download the latest JDBC driver for Databricks

Visit the [Databricks JDBC / ODBC Driver Download](https://www.databricks.com/spark/odbc-drivers-download) page and download the latest version of the JDBC driver and extract the archive.  From that folder unzip the SimbaSparkJDBC42-{version}.zip file as well.  You should now see the SparkJDBC42.jar file. Note the place to this file as we’ll need it later.

### Download and Install DBeaver

You can download and install the latest version of DBeaver from [https://dbeaver.io/download/](https://dbeaver.io/download/)

### Setup the Databricks Driver

Now that you have both the Databricks JDBC driver downloaded and DBeaver installed we can set up the Databricks driver within DBeaver.

From the menu bar click Database > Driver Manager > New.  This will open a dialog box. Fill it in to match the following screenshot.  For the URL Template you can use this string but make sure the httpPath matches the one for your cluster.

jdbc:spark://{host}[:{port}][/{database}];transportMode=http;ssl=1;httpPath={replace with your details};AuthMech=3;

See [JDBC/ODBC drivers and configuration parameters](https://docs.databricks.com/integrations/bi/jdbc-odbc-bi.html) for more information on finding the JDBC details for your given cluster.

Click “Add File” and then choose the path to the file SparkJDBC42.jar which was extracted as part of the JDBC driver download.

### Create Databricks Connection

Now that we have a Databricks driver installed with DBeaver, we can now create a connection to our cluster / database. From the menu bar click Database > New Database Connection. Choose the “Databricks” driver that we created in the previous step and click Next. Enter the values for Host, Port (443), Username, and Password. Once you have the information filled in, you can click “Test Connection” in the lower left to try the connection.

### Generate ERD

Now that we have our connection setup we can connect to our cluster and browse the schemas/databases. In the Projects tab, expand the General > Connections > {your connection name} -- in this case my connection is “Databricks Demo”.

When you click the right arrow (making it a down arrow) it will expand to show you all the databases/schemas in your system.  Select the database you would like to generate an ERD for and press F4.  This will generate a graphical schema.  Here is an example from my demo system using a TPC-DS schema.

For more information please refer to the [ER Diagrams](https://github.com/dbeaver/dbeaver/wiki/ER-Diagrams) section of the DBeaver Wiki.
