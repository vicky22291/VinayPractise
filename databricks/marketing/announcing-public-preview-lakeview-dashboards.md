# Announcing the Public Preview of AI/BI Dashboards!

- Source: https://www.databricks.com/blog/announcing-public-preview-lakeview-dashboards
- Published: 2023-09-28
- Authors: Clark Wildenradt, Chao Cai, Cyrielle Simeone, Erika Ehrli, Ken Wong, Justin Talbot, Miranda Luna, Reynold Xin, Rory Jacobs
- Categories: platform, data-warehousing
- Images: 4 total, 0 extracted as architecture

We are excited to announce the public preview of the next generation of Databricks SQL dashboards, dubbed [AI/BI Dashboards](https://docs.databricks.com/en/dashboards/index.html). Available today, this new dashboarding experience is optimized for ease of use, broad distribution, governance and security.

AI/BI Dashboards provides four major improvements compared to previous generation dashboards:

- **Improved Visualizations:** A new visualization engine delivers beautiful, interactive charts and renders them up to 10x faster.
- **Optimized for sharing and distribution:** Draft/publish capabilities allow you to edit the dashboard freely while your consumers continue to interact with a stable version that they can trust. Securely share with consumers in your organization who may not have direct access to the Databricks workspace.
- **Simplified Design:** With a WYSIWYG user experience and a streamlined information architecture, AI/BI Dashboards now bundle the underlying datasets and widgets together. No more worrying about permissions getting out of sync across referenced Queries.
- **Unification with the Lakehouse:** Governed by Unity Catalog with lineage built-in, so your consumers always know where the insights are coming from.

## The best data warehouse is a lakehouse

[Databricks SQL](https://www.databricks.com/product/databricks-sql) (DBSQL) is a serverless data warehouse on the Lakehouse that lets you run all of your SQL and BI applications at scale with your tools of choice, all at a fraction of the cost of traditional cloud data warehouses. Since launch, analysts have both connected [Databricks SQL warehouses](https://docs.databricks.com/en/sql/admin/create-sql-warehouse.html) to their business intelligence (BI) tools and leveraged the platform's built-in analytics capabilities (SQL query editor, dashboards, and alerts). Increasingly, we've seen customers doing both.

Over the past year, we've continued to [innovate with Databricks SQL](https://www.databricks.com/blog/whats-new-databricks-sql) and we have seen a marked increase in customers reaching for DBSQL dashboards to rapidly generate and share insights throughout the organization as well as to quickly prototype side-by-side with their data before "productionalizing" in a third party BI tool. As DBSQL dashboards usage has ticked up, so have the number of enhancement requests.

We've heard those requests and today are opening the public preview for the solution that addresses them.

## Improved Visualizations

The first thing you will notice the moment you use AI/BI Dashboards is the new color palette and gorgeous visualizations. They look more elegant out of the box, and they also render up to 10x faster for larger charts.

Beyond an improved visual design and faster rendering, the new visualization library also offers more refined behaviors such as sorted tooltips and improved null-value handling. Chart exports also feature transparent backgrounds to make embedding within presentations more professional.

## Optimized for sharing and distribution

AI/BI Dashboards support both the notion of draft/publish and securely sharing to users in the organization that may not have Databricks workspace access.

With the introduction of draft/publish, dashboard authors can iterate on changes without any of that in-progress work interrupting the clean, streamlined version of the dashboard that consumers rely on day-to-day.

AI/BI Dashboard's share to organization feature allows dashboard authors to securely share dashboards with users within their identity provider (IdP) that may not have access to that particular workspace. Taking action on Lakehouse insights is no longer constrained to workspace walls! (Note: This currently relies on the [Unified Login](https://docs.databricks.com/en/administration-guide/users-groups/single-sign-on/index.html#unified-login) & Just-in-Time User Provisioning previews, but will soon be available to all!)

## Simplified Design

AI/BI debuts a redesigned dashboard creation and visualization configuration experience. The new experience allows dashboard designers to make in-place edits directly on the canvas, using the full extent of the data. SQL is optional to get started - search for and select any [Unity Catalog](https://www.databricks.com/product/unity-catalog) table or view - and then apply time bins and aggregations right in the visualization configuration itself.

AI/BI Dashboards also streamlines the underlying information architecture of dashboards. Each AI/BI Dashboard bundles the underlying dataset definitions within the dashboard itself - everything is created, packaged and shared as a unit. This streamlines the lifecycle and permissions management of artifacts when compared to Databricks SQL dashboard historically.

## Unification with the Lakehouse

We heard repeatedly that one of the biggest benefits of building dashboards within the Lakehouse is that doing so allows authors to tap into the benefits of the broader platform.

One way in which we're leaning into this strength is integration into Unity Catalog's automatic [data lineage](https://docs.databricks.com/en/data-governance/unity-catalog/data-lineage.html). Not only are AI/BI Dashboards automatically captured, we've also integrated the lineage feature directly into the published dashboard consumer experience.

We know that two of the most common questions for dashboard users are "Can I trust this data?" and "Where does data come from?" With AI/BI Dashboards, we're making it much easier for business users to answer these questions for themselves.

Of course, because AI/BI Dashboards are available directly as part of the Databricks Lakehouse Platform, there are no extracts to manage, no shadow data warehouse to administrate additionally, no limits on data size and no separate BI servers to scale.

## What's ahead

We have even more exciting updates planned for AI/BI Dashboards in the coming months. Expect rendering and execution performance to continue improving rapidly. Keep an eye out for Git support, embedding, advanced filtering and interactivity controls and more - so stay tuned!

The new AI/BI Dashboards and the legacy DBSQL dashboards will co-exist for some time, but we will eventually consolidate on AI/BI Dashboards.

AI/BI Dashboards are available in public preview today to all [AWS](https://docs.databricks.com/sql/user/dashboards/lakeview-dashboards.html) and [Azure](https://learn.microsoft.com/azure/databricks/sql/user/dashboards/lakeview-dashboards) customers. We anticipate GCP support coming online in the first half of next year. We look forward to seeing what you build!

[Try Databricks](https://www.databricks.com/try-databricks#account)
