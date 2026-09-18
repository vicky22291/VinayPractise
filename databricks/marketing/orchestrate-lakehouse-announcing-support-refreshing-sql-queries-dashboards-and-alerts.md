# Orchestrate the Lakehouse: Announcing Support for Refreshing SQL Queries, Dashboards and Alerts in Databricks Workflows

- Source: https://www.databricks.com/blog/orchestrate-lakehouse-announcing-support-refreshing-sql-queries-dashboards-and-alerts
- Published: 2022-11-10
- Authors: Dino Wernli, Bilal Aslam, Miranda Luna
- Categories: platform, product, data-warehousing
- Images: 3 total, 0 extracted as architecture

[Databricks Workflows](https://www.databricks.com/blog/2022/05/10/introducing-databricks-workflows.html) is the highly available, fully-managed orchestrator for all your data, analytics, and AI workloads. Today, we are happy to announce the public preview of the new SQL task type, which lets you easily author, schedule, inspect, and operate workflows that refresh Databricks SQL queries, dashboards and alerts. You can combine this new task type with existing robust support for notebooks, Python scripts and dbt projects to orchestrate the full power of the lakehouse.

Real-world workflows orchestrate many different activities across the lakehouse. Consider a workflow that ingests data into Delta Lake and transforms it using a Delta Live Table. Once this data is updated, you can now instruct Databricks to refresh one or more dashboards or execute SQL queries. You can also run alerts to check various data quality dimensions and send notifications to Slack or Teams if specified conditions are met. Orchestrating these SQL tasks inside the workflow where data is prepared has several benefits: not only is the workflow easier to reason about, it is also easy to repair and pick up where it failed.

A workflow refreshing multiple queries and a dashboard

In order to create a Databricks SQL task, simply go to Databricks Workflows and select "SQL" from the Type dropdown:

Creating a SQL task to refresh a query

You also benefit from the observability and stability benefits that come with our jobs scheduler such as managing schedules and inspecting previous runs.

Run details for a SQL task

For pricing and availability in your environment, see the Databricks SQL pricing page ([AWS](https://www.databricks.com/product/sql-pricing-aws), [Azure](https://www.databricks.com/product/sql-pricing-azure)).
