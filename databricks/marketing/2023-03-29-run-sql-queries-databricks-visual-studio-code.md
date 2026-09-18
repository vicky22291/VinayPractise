# Run SQL Queries on Databricks From Visual Studio Code

- Source: https://www.databricks.com/blog/2023/03/29/run-sql-queries-databricks-visual-studio-code.html
- Published: 2023-03-29
- Authors: Bilal Aslam, Fabian Jakobs, Shant Hovsepian
- Categories: platform, product, data-warehousing
- Images: 1 total, 0 extracted as architecture

Today, we are excited to announce that users can now run SQL queries on Databricks from within Visual Studio Code via a [preview driver](https://marketplace.visualstudio.com/items?itemName=databricks.sqltools-databricks-driver) for the popular SQLTools extension. This preview release complements the recently launched [public preview](https://www.databricks.com/blog/2023/02/14/announcing-a-native-visual-studio-code-experience-for-databricks.html) of the Databricks extension for VS Code, which allows users to sync and run code developed locally on Databricks-managed compute.

Databricks SQL (DBSQL) is a serverless data warehouse built on the Databricks Lakehouse Platform that enables you to run all of your SQL and BI applications at scale with up to 12x better price and performance compared to legacy data warehouses. DBSQL uses open formats and APIs through a unified governance model with your preferred tools. Now you can connect from VS Code to DBSQL as well as to All Purpose clusters, run SQL queries, and view results without leaving the comfort and power of your favorite editor. This is especially useful if you are working on a [dbt](https://docs.databricks.com/partners/prep/dbt.html) project on Databricks and need to iterate on SQL queries while building data models.

The demo below shows how to install the extension and run a SQL query on Databricks:

We want to thank Matheus Texiera, the author of the popular [SQLTools](https://marketplace.visualstudio.com/items?itemName=mtxr.sqltools) extension and the open-source contributors who have made this extension successful. We would love for you to try this extension out.

Get started by installing the extension from the [VS Code](https://marketplace.visualstudio.com/items?itemName=databricks.databricks). For more information checkout our [documentation](https://docs.databricks.com/dev-tools/sqltools-driver.html?_ga=2.159552637.1759276104.1679290541-50144c0b-3868-4749-bdbf-295fcbee29f4). We welcome your feedback and feature requests on [GitHub](https://github.com/databricks/sqltools-databricks-driver).
